"""Readable history letters; source text and commentary remain distinct."""
import hashlib
import re

VERSION = 'reading-prose-v1'


def paragraphs(text):
    """Only reflow long existing paragraphs at sentence boundaries."""
    blocks = []
    for paragraph in str(text).strip().split('\n'):
        current = ''
        for sentence in re.findall(r'.+?(?:[。！？]|$)', paragraph):
            current += sentence
            if len(current) >= 105:
                blocks.append(current)
                current = ''
        if current:
            blocks.append(current)
    return '\n\n'.join(blocks)


def validate_editorial(story):
    ed = story.get('editorial')
    if ed is None:
        return
    if ed.get('version') != VERSION or ed.get('source_original') != story['original']:
        raise ValueError('润色稿与原文不匹配，须重新审阅')
    for key, low, high in [('title', 8, 50), ('opening', 40, 180),
                           ('reading', 210, 700), ('application', 85, 260), ('closing', 12, 80)]:
        value = ed.get(key)
        if not isinstance(value, str) or not low <= len(value) <= high:
            raise ValueError(f'润色稿 {key} 长度或类型不合格')
    if '\n\n' not in ed['reading'] or len(ed['reading'].split('\n\n')) < 2:
        raise ValueError('解读须形成连贯段落')
    if any(word in ed['application'] for word in ('成功率翻倍', '有效百倍', '今天打卡')):
        raise ValueError('不得使用无依据的效果承诺或打卡套话')


def validate_library(stories):
    seen = {}
    for number, story in stories.items():
        validate_editorial(story)
        ed = story.get('editorial')
        if ed:
            for field in ('opening', 'reading', 'application'):
                value = hashlib.sha256(ed[field].encode()).hexdigest()
                if (field, value) in seen:
                    raise ValueError(f'第{number}篇与第{seen[field, value]}篇重复使用{field}')
                seen[field, value] = number


def build_markdown(number, story, session_label, session_next):
    validate_editorial(story)
    ed = story.get('editorial') or {}
    name = ed.get('title') or story['era']
    title = f'{session_label}·资治通鉴·第{number}篇·{name}'
    lines = [f'## 📚 资治通鉴 · 第{number}篇', f'**{name}**',
             f'{session_label} · {story["vol"]} · {story["dynasty"]}']
    if ed:
        lines.append(ed['opening'])
    lines += ['---', '### 📜 原文', '> ' + story['original'].replace('\n', '\n> '),
              '**白话**', paragraphs(story['translation']), '---', '### 🕯 人物与抉择']
    if ed:
        lines += [ed['reading'], '---', '### 🌿 放到今天', ed['application'], ed['closing']]
    else:
        # Preserve unedited learning material, while removing repeated columns
        # and homework/golden-sentence appendices from the mobile view.
        lines += [paragraphs(story['person']), paragraphs(story['analysis']),
                  '---', '### 🌿 放到今天', paragraphs(story['work']), paragraphs(story['eq'])]
    next_title = story.get('next_title')
    if next_title:
        lines.append(f'下篇：{next_title}')
    lines += [f'📖 {number}/365 · {number/365*100:.1f}% · {session_next}',
              '原文据《资治通鉴》；解读与现代应用为编写。']
    return title, '\n\n'.join(lines)
