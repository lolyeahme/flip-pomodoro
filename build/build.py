# -*- coding: utf-8 -*-
"""组装 flip-pomodoro 单文件应用：内联 FlipClock 依赖、鼓舞人心语录与提示音。"""
import json, re, os, base64

BUILD = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(BUILD)
VENDOR = os.path.join(BUILD, 'vendor')
AUDIO = os.path.join(VENDOR, 'audio')

# 鼓舞人心的中文语录（经典公版格言 + 通用励志语）
QUOTES = [
    "千里之行，始于足下。",
    "锲而不舍，金石可镂。",
    "不积跬步，无以至千里。",
    "宝剑锋从磨砺出，梅花香自苦寒来。",
    "路漫漫其修远兮，吾将上下而求索。",
    "长风破浪会有时，直挂云帆济沧海。",
    "会当凌绝顶，一览众山小。",
    "山重水复疑无路，柳暗花明又一村。",
    "天生我材必有用，千金散尽还复来。",
    "业精于勤，荒于嬉；行成于思，毁于随。",
    "读书破万卷，下笔如有神。",
    "纸上得来终觉浅，绝知此事要躬行。",
    "千磨万击还坚劲，任尔东西南北风。",
    "少年易老学难成，一寸光阴不可轻。",
    "黑发不知勤学早，白首方悔读书迟。",
    "少壮不努力，老大徒伤悲。",
    "莫等闲，白了少年头，空悲切。",
    "志不立，天下无可成之事。",
    "有志者，事竟成。",
    "天行健，君子以自强不息。",
    "一分耕耘，一分收获。",
    "坚持就是胜利。",
    "今天的努力，是明天的底气。",
    "越努力，越幸运。",
    "把平凡的事做到极致，就是不平凡。",
    "所有的坚持，终将美好。",
    "耐心和坚持，会把你带到想去的地方。",
    "你只管努力，剩下的交给时间。",
    "每一次专注，都在向目标靠近。",
    "慢慢来，比较快。",
    "完成比完美更重要。",
    "水滴石穿，不是力量大，而是功夫深。",
    "冰冻三尺，非一日之寒。",
    "只要功夫深，铁杵磨成针。",
    "不积小流，无以成江海。",
    "行百里者半九十。",
    "为者常成，行者常至。",
    "积土而为山，积水而为海。",
    "学如弓弩，才如箭镞。",
    "操千曲而后晓声，观千剑而后识器。",
    "博观而约取，厚积而薄发。",
    "穷且益坚，不坠青云之志。",
    "老骥伏枥，志在千里。",
    "立志欲坚不欲锐，成功在久不在速。",
    "心之所向，素履以往。",
    "道阻且长，行则将至。",
    "行而不辍，未来可期。",
    "星光不问赶路人，时光不负有心人。",
    "努力到无能为力，拼搏到感动自己。",
    "你现在的坚持，藏着你未来的样子。",
    "没有白走的路，每一步都算数。",
    "今天多坚持一点，明天就多从容一点。",
    "专注当下，就是最好的未来。",
    "把大目标拆成小步骤，一步步走完。",
    "每一次开始，都是最好的时机。",
    "沉下心来，把一件事做透。",
]

def main():
    quotes_js = json.dumps(QUOTES, ensure_ascii=False, indent=0).replace('\n', '')

    # 提示音：Kenney 玻璃钟声（CC0），裁尾 + 重采样后的紧凑 WAV，转 data URI 内联
    chime_break = open(os.path.join(AUDIO, 'chime_break.wav'), 'rb').read()
    chime_done = open(os.path.join(AUDIO, 'chime_done.wav'), 'rb').read()
    chime_break_uri = 'data:audio/wav;base64,' + base64.b64encode(chime_break).decode('ascii')
    chime_done_uri = 'data:audio/wav;base64,' + base64.b64encode(chime_done).decode('ascii')

    tpl = open(os.path.join(BUILD, 'app.template.html'), encoding='utf-8').read()

    # 已内联的依赖：FlipClock.js 0.10.8（MIT）样式与脚本
    css = open(os.path.join(VENDOR, 'flipclock.css'), encoding='utf-8').read()
    js = open(os.path.join(VENDOR, 'flipclock.min.js'), encoding='utf-8').read()
    js = re.sub(r'//# sourceMappingURL=.*$', '', js).strip()

    assert '</style' not in css.lower(), 'CSS 含 </style>'
    assert '</script' not in js.lower(), 'JS 含 </script>'

    out = tpl.replace('/*__FLIPCLOCK_CSS__*/', css) \
             .replace('/*__FLIPCLOCK_JS__*/', js) \
             .replace('/*__QUOTES__*/', quotes_js) \
             .replace('/*__CHIME_BREAK__*/', chime_break_uri) \
             .replace('/*__CHIME_DONE__*/', chime_done_uri)

    out_path = os.path.join(BASE, 'index.html')
    open(out_path, 'w', encoding='utf-8', newline='\n').write(out)

    # 校验未残留占位符
    for token in ['__FLIPCLOCK_CSS__', '__FLIPCLOCK_JS__', '__QUOTES__',
                  '__CHIME_BREAK__', '__CHIME_DONE__']:
        assert token not in out, '占位符未替换: ' + token

    print('quotes:', len(QUOTES))
    print('chime_break:', len(chime_break), 'bytes; chime_done:', len(chime_done), 'bytes')
    print('index.html bytes:', os.path.getsize(out_path))
    print('single-file OK')

if __name__ == '__main__':
    main()
