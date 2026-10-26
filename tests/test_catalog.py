import importlib.util
import pathlib
import unittest

PATH = pathlib.Path(__file__).resolve().parents[1] / 'scripts' / 'sync_public_catalog.py'
spec = importlib.util.spec_from_file_location('catalog_sync', PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class PublicIndexTests(unittest.TestCase):
    def setUp(self):
        self.work = {'id':'unknown','title':'關於未知的我們','url':'https://unknown-archive.pages.dev/'}

    def test_unknown_serial_url(self):
        row = {'work':'serial','slug':'separate','title':'無法抵抗的本意','cp':['魏之遠 × 魏謙']}
        values = mod.normalize('unknown', self.work, [row])
        self.assertEqual(values[0]['readUrl'], 'https://unknown-archive.pages.dev/#read/serial/separate')
        self.assertNotIn('blocks', values[0])

    def test_draft_not_indexed(self):
        rows = [{'work':'shorts','slug':'hurt','title':'受傷','status':'草稿'}]
        self.assertEqual(mod.normalize('unknown', self.work, rows), [])

    def test_private_checkbox_not_indexed(self):
        rows = [{'work':'shorts','slug':'hurt','title':'受傷','網站公開':False}]
        self.assertEqual(mod.normalize('unknown', self.work, rows), [])

    def test_does_not_copy_body_or_token(self):
        rows = [{'work':'shorts','slug':'hurt','title':'受傷','blocks':[{'text':'PRIVATE BODY'}],'NOTION_TOKEN':'secret'}]
        values = mod.normalize('unknown', self.work, rows)
        self.assertNotIn('blocks', values[0]); self.assertNotIn('NOTION_TOKEN',values[0]);self.assertNotIn('PRIVATE BODY',str(values))

    def test_malformed_slug_not_indexed(self):
        rows = [{'work':'shorts','slug':'javascript:alert(1)','title':'受傷'}]
        self.assertEqual(mod.normalize('unknown', self.work, rows), [])

    def test_first_note_route(self):
        work={'id':'first-note','title':'戀習曲','url':'https://first-note-of-love.pages.dev/'}
        self.assertEqual(mod.normalize('first-note', work, [{'id':'story-1','order':1,'title':'A','status':'已發布','published':True}])[0]['readUrl'], 'https://first-note-of-love.pages.dev/')

    def test_first_note_without_slug_indexed(self):
        work = {'id':'first-note','title':'彈一場完美戀愛','url':'https://first-note-of-love.pages.dev/'}
        rows = [{'id':'100','order':12,'title':'勇氣','published':True,'status':'已發布',
                 'cp':['Neil × Sea'], 'content':'正文不應進索引'}]
        result = mod.normalize('first-note',work,rows)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['title'], '勇氣')
        self.assertEqual(result[0]['section'], '戀習曲')
        self.assertEqual(result[0]['workId'], 'first-note')
        self.assertNotIn('content', result[0])

    def test_first_note_drafts_not_indexed(self):
        work = {'id':'first-note','title':'彈一場完美戀愛','url':'https://first-note-of-love.pages.dev/'}
        rows = [{'id':'1','order':1,'title':'草稿','published':False,'status':'草稿'},
                {'id':'2','order':2,'title':'網站私密','published':False,'status':'已發布'},
                {'id':'3','order':3,'title':'發布不合','published':True,'status':'草稿'},
                {'id':'4','order':4,'title':'未註記公開','status':'已發布'}]
        self.assertEqual(mod.normalize('first-note',work,rows), [])

    def test_love_casting_route(self):
        work={'id':'love-casting','title':'戀愛 Casting','url':'https://love-casting.pages.dev/'}
        self.assertEqual(mod.normalize('love-casting', work, [{'slug':'story-1','title':'A'}])[0]['readUrl'], 'https://love-casting.pages.dev/#/read/story-1')

    def test_topgun_route(self):
        work={'id':'top-gun','title':'Top Gun','url':'https://top-gun-archive.pages.dev/'}
        got=mod.normalize('top-gun',work,[{'work':'song_maketh_wingman','slug':'song-one','title':'One'}])
        self.assertEqual(got[0]['readUrl'],'https://top-gun-archive.pages.dev/#read/song_maketh_wingman/song-one')

    def test_unknown_structure_rejected(self):
        with self.assertRaises(ValueError): mod.public_rows({'data':[]})

if __name__=='__main__':unittest.main()
