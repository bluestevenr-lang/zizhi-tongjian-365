import copy
import unittest
from unittest.mock import patch
import push
from editorial import build_markdown, validate_library, validate_editorial


class EditorialTests(unittest.TestCase):
    def test_entire_history_library_renders_with_sources_and_progress(self):
        validate_library(push.CONTENT)
        self.assertEqual(len([x for x in push.CONTENT.values() if x.get('editorial')]),12)
        for number,story in push.CONTENT.items():
            before=copy.deepcopy(story)
            title,text=build_markdown(number,story,'晨读','午读继续')
            self.assertIn('资治通鉴',title)
            self.assertIn(story['original'],text.replace('\n> ','\n'))
            self.assertIn(f'{number}/365',text)
            self.assertNotIn('### 📝 学习方法',text)
            self.assertNotIn('### ✨ 金句',text)
            self.assertLess(len(text),push.MAX_MARKDOWN_CHARS)
            self.assertEqual(story,before)

    def test_mismatched_source_or_repeated_new_analysis_is_rejected(self):
        story=copy.deepcopy(push.CONTENT[310]);story['original']+='改字'
        with self.assertRaises(ValueError):validate_editorial(story)
        pair={n:copy.deepcopy(push.CONTENT[n]) for n in (310,311)}
        pair[311]['editorial']['reading']=pair[310]['editorial']['reading']
        with self.assertRaises(ValueError):validate_library(pair)

    def test_failed_send_never_advances_progress(self):
        with patch.object(push,'story_num',310),patch.object(push,'last_num',309),\
             patch.object(push,'send_markdown',side_effect=RuntimeError('delivery failed')),\
             patch.object(push,'save_last') as save:
            with self.assertRaises(RuntimeError):push.main()
            save.assert_not_called()

    def test_successful_send_uses_new_prose_and_then_advances_once(self):
        with patch.object(push,'story_num',310),patch.object(push,'last_num',309),\
             patch.object(push,'send_markdown') as send,patch.object(push,'save_last') as save:
            push.main()
            send.assert_called_once()
            self.assertIn(push.CONTENT[310]['editorial']['title'],send.call_args.args[1])
            save.assert_called_once_with(310)

    def test_republish_keeps_progress(self):
        with patch.object(push,'last_num',311),patch.object(push,'send_markdown') as send,patch.object(push,'save_last') as save:
            push.main(['--republish-last'])
            self.assertIn(push.CONTENT[311]['editorial']['title'],send.call_args.args[1])
            save.assert_not_called()


if __name__=='__main__' :unittest.main()
