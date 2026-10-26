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


if __name__ == '__main__':
    unittest.main()
