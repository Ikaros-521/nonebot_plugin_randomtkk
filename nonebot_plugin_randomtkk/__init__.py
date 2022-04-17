from nonebot import on_command
from nonebot.typing import T_State
from nonebot.matcher import Matcher
from nonebot.adapters.onebot.v11 import Message, MessageSegment, GroupMessageEvent
from nonebot.params import Depends, CommandArg, State
from nonebot.rule import Rule
from .handler import random_tkk_handler

__randomtkk_vsrsion__ = "v0.1.0"
__randomtkk_notes__ = f'''
随机唐可可 {__randomtkk_vsrsion__}
[随机唐可可] 后接[简单/普通/困难/地狱/自定义数量]开启唐可可挑战
不指定难度默认普通模式
支持[随机鲤鱼/鲤鱼王/Liyuu/liyuu]
答案格式：[答案是][行][空格][列]
例如：答案是114 514
'''.strip()

def unique_check(event: GroupMessageEvent) -> bool:
    return random_tkk_handler.check_tkk_playing(str(event.group_id))

random_tkk = on_command(cmd="随机唐可可", aliases={"随机鲤鱼", "随机鲤鱼王", "随机Liyuu", "随机liyuu"}, priority=12)
guess_tkk = on_command(cmd="答案是", rule=Rule(unique_check), priority=12, block=True)
over_tkk = on_command(cmd="找不到唐可可", aliases={"唐可可人呢", "呼叫鲤鱼姐"}, rule=Rule(unique_check), priority=12, block=True)
 
@random_tkk.handle()
async def _(matcher: Matcher, event: GroupMessageEvent, args: Message = CommandArg()):
    gid = str(event.group_id)
    if random_tkk_handler.check_tkk_playing(gid):
        await matcher.finish("游戏已经开始啦！", at_sender=True)
        
    args = args.extract_plain_text().strip().split()

    if not args:
        await matcher.send("未指定难度，默认普通模式")
        level = "普通"
    elif args and len(args) == 1: 
        if args[0] == "帮助":
            await matcher.finish(__randomtkk_notes__)
        level = args[0]
    else:
        await matcher.finish("参数太多啦~")
        
    img_file, waiting = await random_tkk_handler.one_go(gid, level)
    
    await matcher.send(MessageSegment.image(img_file))
    await matcher.send(f"将在 {waiting}s 后公布答案\n答案格式：[答案是][行][空格][列]\n例如：答案是114 514")
    
    random_tkk_handler.start_timer(matcher, gid, waiting)
    

async def get_user_guess(args: Message = CommandArg(), state: T_State = State()):
    args = args.extract_plain_text().strip().split()

    if not args:
        await guess_tkk.finish("答案是啥捏？")
    elif args and len(args) == 1:    
        await guess_tkk.finish("答案格式错误~")
    elif args and len(args) == 2:
        args = [int(x) for x in args]   # 类型转换str -> int
        return {**state, "guess": args}
    else:
        await guess_tkk.finish("参数太多啦~")

@guess_tkk.handle()
async def _(event: GroupMessageEvent, state: T_State = Depends(get_user_guess)): 
    gid = str(event.group_id)
    pos = state["guess"]

    if random_tkk_handler.check_answer(gid, pos) is True:
        random_tkk_handler.close_game(gid)
        await guess_tkk.finish("答对啦，好厉害！", at_sender=True)
    else:
        await guess_tkk.finish("不对哦~", at_sender=True)
        
@over_tkk.handle()
async def _(matcher: Matcher, event: GroupMessageEvent):
    gid = str(event.group_id)
    
    result = await random_tkk_handler.over_game(matcher, gid)
    if not result:
        await matcher.finish("提前结束游戏出错……")