from pathlib import Path
import re
import tempfile
import unittest

from gcov_to_sample import convert, gcno_paths

FIXTURE=Path(__file__).resolve().parent/'fixture'


class TestGcovSample(unittest.TestCase):
    def test_both_directions(self):
        for tag,left,right in (('left',99900,100),('right',100,99900)):
            with self.subTest(profile=tag):
                profile,audit=convert(FIXTURE/'layout.gcno',FIXTURE/f'{tag}.dump')
                self.assertEqual(profile,(FIXTURE/f'{tag}.prof').read_text())
                choose=audit['choose@layout.c:7']
                self.assertEqual(choose['head'],100000)
                self.assertEqual(choose['body'][3],left)
                self.assertEqual(choose['body'][7],right)
                self.assertEqual(audit['left@layout.c:19']['head'],left)
                self.assertEqual(audit['right@layout.c:24']['head'],right)

    def test_ambiguous_linkage_exclusion(self):
        profile,audit=convert(FIXTURE/'layout.gcno',FIXTURE/'left.dump',{'choose'})
        self.assertNotIn('choose:',profile)
        self.assertEqual(audit['choose@layout.c:7']['skipped'],'ambiguous_or_unsupported_function_name')

    def test_format_and_pairing_errors(self):
        with tempfile.TemporaryDirectory() as d:
            d=Path(d)
            corrupt=d/'bad.gcno'
            notes=(FIXTURE/'layout.gcno').read_bytes()
            corrupt.write_bytes(notes[:4]+b'*804'+notes[8:])
            with self.assertRaisesRegex(ValueError,'B11'):
                gcno_paths(corrupt)
            corrupt.write_bytes(notes[:-16])
            with self.assertRaises(ValueError):
                gcno_paths(corrupt)
            dump=d/'bad.dump'
            dump.write_text((FIXTURE/'left.dump').read_text().replace('choose (0)','changed (0)',1))
            with self.assertRaisesRegex(ValueError,'does not match'):
                convert(FIXTURE/'layout.gcno',dump)

    def test_compiler_consumption_and_layout(self):
        for tag,expected,weights in (('left','left',(99900,100)),('right','right',(100,99900))):
            with self.subTest(profile=tag):
                yaml=(FIXTURE/f'{tag}.opt.yaml').read_text()
                records=[segment for segment in yaml.split('---') if re.search(r'^Name:\s+AppliedSamples$',segment,re.M)
                         and re.search(r'^Function:\s+choose$',segment,re.M)]
                positive=[int(m) for x in records for m in re.findall(r"NumSamples:\s+'(\d+)'",x)]
                self.assertIn(100000,positive)
                self.assertIn(99900,positive)
                ir=(FIXTURE/f'{tag}.ll').read_text()
                self.assertIn(f'!"branch_weights", i32 {weights[0]}, i32 {weights[1]}',ir)
                asm=(FIXTURE/f'{tag}.choose.asm').read_text()
                self.assertEqual(re.findall(r'\bcallq\s+(left|right)',asm)[0],expected)

    def test_noinstr_excluded_in_a32(self):
        fn, files=gcno_paths(FIXTURE/'arm-noinstr.gcno')
        self.assertEqual({value.name for value in fn.values()},{'ordinary'})
        self.assertEqual(files,('arm-noinstr.c',))


if __name__=='__main__':
    unittest.main()
