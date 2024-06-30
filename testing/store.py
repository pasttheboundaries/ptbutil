import unittest
import os
import shutil
from ptbutil.store.textdepo import TextDepo, textdepo_hash, TextDepoIndex, FileDescriptor


class TestTextDepo(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory for testing
        self.test_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'temp_store')
        os.mkdir(self.test_dir)
        self.text_depo = TextDepo(self.test_dir, file_name="test_depo")

    def tearDown(self):
        # Remove the temporary directory after tests
        shutil.rmtree(self.test_dir)

    def test_textdepo_hash(self):
        text = "test string"
        self.assertEqual(type(textdepo_hash(text)), str)

    def test_file_descriptor(self):
        fd = FileDescriptor(hash="1", len=10, time="20240630T120000", filename="test.txt")
        self.assertEqual(fd.as_dict(), {
            "hash": "1",
            "len": 10,
            "time": "20240630T120000",
            "filename": "test.txt"
        })

    def test_write_and_read(self):
        text = "Test content"
        self.text_depo.write(text)
        self.assertEqual(len(self.text_depo.index), 1)

        # Read the file using the condition (filename contains 'test_depo')
        read_content = self.text_depo.read(condition="test_depo")
        self.assertEqual(read_content, text)

    def test_write_many_and_read_many(self):
        texts = ["Text 1", "Text 2", "Text 3"]
        self.text_depo.write_many(texts)
        self.assertEqual(len(self.text_depo.index), 3)

        read_texts = list(self.text_depo.read_many(condition="test_depo"))
        self.assertEqual(len(read_texts), 3)
        self.assertIn("Text 1", read_texts)
        self.assertIn("Text 2", read_texts)
        self.assertIn("Text 3", read_texts)

    def test_drop_duplicates(self):
        text = "Duplicate content"
        self.text_depo.write(text)
        self.text_depo.write(text)  # Writing the same content again
        self.assertEqual(len(self.text_depo.index), 1)  # Should still be 1

    def test_invalid_directory(self):
        with self.assertRaises(FileNotFoundError):
            TextDepo("/non/existent/directory")

    def test_read_non_existent_file(self):
        with self.assertRaises(FileNotFoundError):
            self.text_depo.read(filename="non_existent.txt")

    def test_read_without_filename_or_condition(self):
        with self.assertRaises(ValueError):
            self.text_depo.read()

    def test_text_depo_index(self):
        index = TextDepoIndex(os.path.join(self.test_dir, "test_index"))
        index.set("key1", "value1")
        self.assertEqual(index.get("key1"), "value1")
        self.assertTrue("key1" in index)
        self.assertEqual(len(index), 1)


if __name__ == '__main__':
    unittest.main()