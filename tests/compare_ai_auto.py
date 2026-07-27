"""快速对比：引擎 vs DeepSeek 自动统计"""
import json, re

with open('tests/engine_results.json', 'r', encoding='utf-8') as f:
    engine = json.load(f)

with open('tests/ai_response.txt', 'r', encoding='utf-8') as f:
    text = f.read()

# 解析AI回复
blocks = re.split(r'\n(?=\d+\.\s)', text.strip())
ai = {}
for b in blocks:
    lines = b.strip().split('\n')
    name = ''
    sw = ''
    gods = []
    for line in lines:
        m = re.match(r'\d+\.\s+(.+?)(?:（|$)', line)
        if m:
            name = m.group(1).strip()
        if '身强弱' in line or '身强弱' in line:
            sw = line.split('：')[-1].strip() if '：' in line else ''
        if line.startswith('用神') and '：' in line:
            gods = [g.strip() for g in line.split('：')[1].replace('、', ',').split(',')]
    if name:
        ai[name] = {'sw': sw, 'gods': set(gods)}

# 对比
sw_ok = 0
god_ok = 0
for e in engine:
    name = e['name']
    if name not in ai:
        continue
    a = ai[name]
    esw = e['strong_weak']
    # 强弱宽松匹配（如"偏强"包含"强"）
    if esw[:2] in a['sw'] or a['sw'][:2] in esw:
        sw_ok += 1
    else:
        print(f"  ❌ 强弱: {name:8s} 引擎={esw:4s}  AI={a['sw']}")
    # 用神至少一个重叠
    eg = set(e['useful_god'])
    if eg & a['gods']:
        god_ok += 1
    else:
        print(f"  ❌ 用神: {name:8s} 引擎={eg}  AI={a['gods']}")

print(f"\n{'='*50}")
print(f"对比结果：{len(engine)}位名人")
print(f"强弱一致: {sw_ok}/{len(engine)} ({sw_ok/len(engine)*100:.0f}%)")
print(f"用神一致: {god_ok}/{len(engine)} ({god_ok/len(engine)*100:.0f}%)")