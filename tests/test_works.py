import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('works_sync', ROOT / 'scripts' / 'sync_notion_works.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def rt(value):
    return {'type':'rich_text','rich_text':[{'plain_text':value}]}


def title(value):
    return {'type':'title','title':[{'plain_text':value}]}


def select(value):
    return {'type':'select','select': {'name':value}}


def mock_page(name, code, original, checked=True, url='https://unknown-archive.pages.dev/'):
    return {'properties':{
        '作品名':title(name),'作品識別碼':rt(code),'原著分類':select(original),
        '總站顯示':{'type':'checkbox','checkbox':checked},
        '作品網站網址':{'type':'url','url':url},'網站狀態':select('已上線'),
        '英文顯示名稱':rt('English'),'總站排序':{'type':'number','number':7}
    }}


class WorkGroupingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import json
        cls.collections = json.loads((ROOT / 'data' / 'collections.json').read_text())['collections']

    def test_two_unknown_works_one_category(self):
        pages = [mock_page('短篇集','unknown_shorts','關於未知的我們'),
                 mock_page('The Distance Between Us','the_distance_between_us','關於未知的我們')]
        records = mod.build_works(pages,self.collections)
        self.assertEqual(len(records),2)
        self.assertEqual({x['collectionId'] for x in records},{'unknown'})

    def test_unchecked_is_not_exported(self):
        page = mock_page('私人草稿','private','關於未知的我們',False)
        self.assertEqual(mod.build_works([page],self.collections),[])

    def test_original_category(self):
        page = mock_page('戀習曲','first-note-of-love','彈一場完美戀愛')
        self.assertEqual(mod.to_work(page,self.collections)['collectionId'],'first-note')

    def test_duplicate_slug_rejected(self):
        one = mock_page('短篇集','duplicate','關於未知的我們')
        two = mock_page('連載','duplicate','關於未知的我們')
        with self.assertRaises(ValueError):
            mod.build_works([one,two],self.collections)

    def test_metadata_has_no_page_body_or_secret(self):
        page = mock_page('受傷','hurt','關於未知的我們')
        page['blocks'] = [{'text':'private body'}]
        page['id'] = 'secret_not_public'
        record = mod.to_work(page,self.collections)
        self.assertNotIn('blocks',record)
        self.assertNotIn('id' if False else 'pageId',record)
        self.assertNotIn('private body',str(record))
        self.assertNotIn('secret_not_public',str(record))

    def test_invalid_site_url_rejected(self):
        page = mock_page('短篇集','shorts','關於未知的我們',True,url='javascript:alert(1)')
        record = mod.to_work(page,self.collections)
        self.assertEqual(record['status'],'planned')
        self.assertIsNone(record['url'])

    def test_unknown_classification_fails_for_opted_in_works(self):
        page = mock_page('新作品','work-1','不存在的原著')
        with self.assertRaises(ValueError):
            mod.to_work(page,self.collections)

    def test_mixed_titles_become_one_parent(self):
        originals = ['夏日最後的秘密', '路過我年少時光的藍色', '對立而已', 'JimmyOhm', 'TopForm']
        expected = ['summer-secret', 'blue-youth', 'opposites', 'jimmyohm', 'top-form']
        pages = [mock_page(name, f'work_{i}', name) for i, name in enumerate(originals)]
        records = mod.build_works(pages, self.collections)
        self.assertEqual(len(records), 5)
        self.assertEqual([r['collectionId'] for r in records], ['misc'] * 5)
        self.assertEqual({r['subcategoryId'] for r in records}, set(expected))

    def test_mixed_work_with_explicit_parent_and_title(self):
        page = mock_page('TopForm', 'top-form-unique', '綜合作品')
        work = mod.to_work(page, self.collections)
        self.assertEqual(work['collectionId'], 'misc')
        self.assertEqual(work['subcategoryId'], 'top-form')

    def test_mixed_work_no_subcategory_still_in_misc(self):
        page = mock_page('未分類的短篇', 'random-short', '綜合作品')
        work = mod.to_work(page, self.collections)
        self.assertEqual(work['collectionId'], 'misc')
        self.assertNotIn('subcategoryId', work)

    def test_new_sections_resolve_correctly(self):
        for original, expected in [('心機','shin-ji'), ('Double Shuffle','shin-ji'),
                                   ('四手聯彈，兩首奏鳴曲','four-hands'),
                                   ('Four Hands, Two Sonatas','four-hands')]:
            self.assertEqual(mod.to_work(mock_page(original,'slug-'+expected,original),self.collections)['collectionId'],expected)

    def test_rwrb_shows_complete_title(self):
        full = next(cat for cat in self.collections if cat['id'] == 'rwrb')
        self.assertIn('Red, White & Royal Blue', full['title'])
        self.assertEqual(mod.to_work(mock_page('作品','rwrb-story','RWRB'),self.collections)['collectionId'],'rwrb')

    def test_updated_display_names_and_backward_compatible_aliases(self):
        by_id = {c['id']: c for c in self.collections}
        self.assertEqual(by_id['shin-ji']['title'], '心機')
        self.assertEqual(by_id['shin-ji']['english'], 'Double Shuffle')
        self.assertEqual(by_id['four-hands']['title'], '八分音符')
        self.assertEqual(by_id['four-hands']['english'], 'Quaver')
        self.assertEqual(by_id['rwrb']['title'], 'Red, White & Royal Blue')
        self.assertNotIn('（RWRB）', by_id['rwrb']['title'])
        self.assertIn('RWRB', by_id['rwrb']['aliases'])

    def test_quaver_existing_notion_original_classification(self):
        for original in ('四手聯彈', '四手聯彈，兩首奏鳴曲', '八分音符', 'Quaver'):
            work = mod.to_work(mock_page('Quaver', 'quaver', original), self.collections)
            self.assertEqual(work['collectionId'], 'four-hands')
        # This work's Notion checkbox is currently unchecked; do not index it yet.
        self.assertIsNone(mod.to_work(mock_page('Quaver', 'quaver', '四手聯彈', False), self.collections))

    def test_bitter_sweet_double_shuffle(self):
        work = mod.to_work(mock_page('苦盡甘來未必來', 'bittersweet', '心機'), self.collections)
        self.assertEqual(work['collectionId'], 'shin-ji')

    def test_fallback_detects_quaver_when_json_alias_missing(self):
        import copy
        copies = copy.deepcopy(self.collections)
        collection = next(c for c in copies if c['id'] == 'four-hands')
        collection['aliases'] = []
        # 複製一個舊版 JSON：名稱尚未改成「八分音符」也必須能正常同步
        collection['title'] = 'Four Hands, Two Sonatas'
        page = mock_page('Quaver', 'quaver', '四手聯彈')
        self.assertEqual(mod.to_work(page, copies)['collectionId'], 'four-hands')

    def test_alias_variations_for_four_hands(self):
        for label in ('四手聯彈', '四手联弹', '四手聯彈、兩首奏鳴曲', '八分音符', 'Quaver'):
            record = mod.to_work(mock_page('Quaver','quaver',label), self.collections)
            self.assertEqual(record['collectionId'], 'four-hands')

    def test_misc_fallback_keeps_all_five_subcategories(self):
        import copy
        categories = copy.deepcopy(self.collections)
        misc = next(c for c in categories if c['id'] == 'misc')
        for sub in misc['subcategories']:
            sub['aliases'] = []
        for label, subcategory in [
            ('夏日最後的秘密','summer-secret'),
            ('路過我年少時光的藍色','blue-youth'),
            ('對立而已','opposites'),
            ('JimmyOhm','jimmyohm'),
            ('TopForm','top-form'),
        ]:
            record = mod.to_work(mock_page(label,'test-'+subcategory,label), categories)
            self.assertEqual(record['collectionId'], 'misc')
            self.assertEqual(record['subcategoryId'], subcategory)

    def test_exact_number_of_top_level_sections(self):
        self.assertEqual(len(self.collections), 11)
        self.assertEqual(len([s for cat in self.collections for s in cat.get('subcategories', [])]), 5)
        self.assertEqual(len(set(c['index'] for c in self.collections)), 11)


if __name__ == '__main__':
    unittest.main()
