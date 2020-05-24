'''
功能基于yobot custom.py&jjc_consult.py代码进行编写
'''

import asyncio, re, time, random, string, os, requests
from typing import Any, Dict, Union
from .clanjob_data import dor, logs
from aiocqhttp.api import Api
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from quart import Quart

class clanjob:
    def __init__(self,
                 glo_setting: Dict[str, Any],
                 scheduler: AsyncIOScheduler,
                 app: Quart,
                 bot_api: Api,
                 *args, **kwargs):

        # 这是来自yobot_config.json的设置，如果需要增加设置项，请修改default_config.json文件
        self.setting = glo_setting

        # 这是cqhttp的api，详见cqhttp文档
        self.api = bot_api

        #自定义admin用于非管理员用户有权限删除他人作业
        self.extraAdmin = ()
        #=====================此处功能为关闭了yobot jjc_consult时使用的，如果没有关闭请手动的注释相关代码======================
        self.nickname_dict: Dict[str, Tuple[str, str]] = {}

        Nicknames_csv = "https://gitee.com/yobot/pcr-nickname/raw/master/nicknames.csv"
        nickfile = os.path.join(glo_setting["dirname"],"nickname3.csv")
        if not os.path.exists(nickfile):
            res = requests.get(Nicknames_csv)
            if res.status_code != 200:
                raise ServerError(
                    "bad server response. code: "+str(res.status_code))
            with open(nickfile, "w", encoding="utf-8-sig") as f:
                f.write(res.text)
        with open(nickfile, encoding="utf-8-sig") as f:
            csv = f.read()
            for line in csv.split("\n")[1:]:
                row = line.split(",")
                for col in row:
                    self.nickname_dict[col] = (row[0], row[1])
        #=================================================================================================================

    async def execute_async(self, ctx: Dict[str, Any]) -> Union[None, bool, str]:

        def unitintout(nickname):
            try:
                unitintdata = self.nickname_dict[nickname]
                return int(unitintdata[0])
            except:
                return nickname 

        def getjobid(d):
            if d == 'set':
                return ''.join(random.sample(string.ascii_letters + string.digits, 4))
            if d == 'delete':
                return ''.join(random.sample(string.ascii_letters + string.digits, 8))

        def getunitintlist(msgdata):
            unitintlist = []
            for nickname in msgdata.split():#处理nickname里附带了rank和星数据，转换为unitid
                nickname = re.match(r'^[\u4e00-\u9fa5]*[^a-z0-9]',nickname).group()
                unitintlist.append(unitintout(nickname))
            try:
                unitintlistcopy = unitintlist
                unitintlist.sort()
                return unitintlist
            except:#排序的时候出现错误，未指定错误nama
                names = ''
                for s in unitintlistcopy:
                    if not isinstance(s,int):
                        names += f'{s} '
                return f'队伍昵称输入有误,没有找到【{names}】'

        def setdata(context):#写作业
            msgdata = re.findall(r'^写([ABCDabcd][1-5])的?作业([\s\S]*[^0-9])([0-9]*[wW万])(留言[\S]*)?',context['raw_message'])
            try:
                bossid,team,dmg,msg = ','.join(msgdata[0]).split(',')
                #print (bossid,team,dmg,msg)
            except BaseException:
                print('error')
                return
            unitintlist = getunitintlist(team)
            print (unitintlist)
            if '昵称输入有误' in unitintlist:
                return unitintlist
            gid = context['group_id']
            try:
                dorint = dor.raw(
                    f'select * from "dor" WHERE "group_id" = "{gid}" AND "bossid" = "{bossid}" AND "team_int" = "{unitintlist}"'
                    )
                s = dorint.get()
                if s != None:
                    return '作业已存在'
            except dor.DoesNotExist:
                jobid = getjobid('set')
                dor.create(
                    group_id=context['group_id'],
                    pr_user_id=context['user_id'],
                    bossid=bossid,
                    team=team,
                    team_int=unitintlist,
                    dmg=dmg,
                    msg=(None if msg == '' else msg),
                    jobid=f'{jobid}'
                    )
                return '作业写入'

        def getdata(context):#查作业
            msgdata = re.findall(r'^查([ABCDabcd][1-5])的?作业',context['raw_message'])
            bossid = ','.join(msgdata).split(',')
            joblist = dor.select(dor.team, dor.dmg).where(dor.group_id == context['group_id'],dor.bossid == bossid[0])
            username = context['sender'].get('card')
            out_msg = f'>{username}'
            for s in dor.select().where((dor.group_id == context['group_id'])&(dor.bossid == bossid[0])):
                msg = ('' if s.msg == None else s.msg)
                out_msg += f'\n{s.jobid}|{s.team}|{s.dmg}|{msg}'
            if not out_msg == '':
                return out_msg
            return f'没有找到{bossid}的作业，赶紧写一点成为大佬吧。'

        def deldata(context):#删
            if re.match(r'^删除[\s\S{4}]*作业',context['raw_message']):
                gid = context['group_id']
                try:
                    msglist = re.findall(r'删除([a-zA-Z0-9]{4})作业',context['raw_message'])
                    jobid = (msglist[0])
                except BaseException:
                    return '需要以【删除<作业代号>作业】的形式进行发送'
                getid = dor.raw(
                    f'select * from "dor" where "group_id" = "{gid}" and "jobid" = "{jobid}"'
                )
                deljobid = getjobid('delete')
                jobidset = dor.update(jobdelcode=deljobid,jobDelTimeLine=f'{round(time.time())+180}').execute()
                return f'删除码3分钟有效，确认删除请输入【确认删除{deljobid}】即可删除作业'
            if re.match(r'^确认删除[\s\S{8}]',context['raw_message']):
                #print(context)
                gid = context['group_id']
                userGlevel = context['sender'].get('role')
                try:
                    delecode = re.search(r'([a-zA-Z0-9]{8})',context['raw_message']).group()
                    #print(delecode)
                    data = dor.get(group_id = gid,jobdelcode = delecode)
                    if data.jobDelTimeLine > time.time():
                        if data.pr_user_id == context['user_id'] or userGlevel == 'admin' or userGlevel == 'owner' or context['user_id'] in self.extraAdmin:# or context['userlevel'] >= 3:需要修改的权限验证
                            dor.delete().where(dor.group_id==gid,dor.jobdelcode==delecode).execute()
                            logs.create(group_id=gid,user_id=context['user_id'],jobdelcode=delecode,jobDelTime=time.time())
                            return '删除成功'
                        else :
                            return '权限不足无法删除他人作业'
                    else:
                        return '超过删除可执行时限，请重新获取删除码'
                except (IndexError,dor.DoesNotExist):
                    return '作业id不存在'
                except TypeError:
                    out_msg = context['raw_message'][4:]
                    return f'「{out_msg}」为错误的作业id'

        cmd = ctx['raw_message']
        if re.match(r'^[查写删][\s\S]*作业|确认删除',cmd) and ctx['message_type'] == 'group':
            if re.match(r'^查[\s\S]*作业', cmd):
                await self.api.send_group_msg(group_id=ctx['group_id'], message=f'{getdata(ctx)}')
            if re.match(r'^写[\s\S]*作业', cmd):
                await self.api.send_group_msg(group_id=ctx['group_id'], message=f'{setdata(ctx)}')
            if re.match(r'^(删除|确认删除)[\s\S]*', cmd):
                await self.api.send_group_msg(group_id=ctx['group_id'], message=f'{deldata(ctx)}')

        return False
