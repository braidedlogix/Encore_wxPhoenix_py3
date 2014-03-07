#
# (C) Copyright 2014 Enthought, Inc., Austin, TX
# All right reserved.
#
# This file is open source software distributed according to the terms in LICENSE.txt
#

from unittest import TestCase
import time

import encore.storage.tests.abstract_test as abstract_test
from ..mounted_store import MountedStore
from ..dict_memory_store import DictMemoryStore
from ..string_value import StringValue

class MountedStoreTest(TestCase):

    def setUp(self):
        super(MountedStoreTest, self).setUp()
        self.mounted_store = DictMemoryStore()
        self.backing_store = DictMemoryStore()
        t = time.time()
        self.mounted_store._store['test1'] = (
            'mounted\n', {'metakey': 'mounted'}, t, t
        )
        self.backing_store._store['test/test1'] = (
            'backing\n', {'metakey': 'backing',}, t, t
        )
        self.backing_store._store['test/test2'] = (
            'backing\n', {'metakey': 'backing',}, t, t
        )
        self.store = MountedStore('test/', self.mounted_store, self.backing_store)

    def test_get_masked(self):
        value = self.store.get('test/test1')
        self.assertEqual(value.data.read(), "mounted\n")
        self.assertEqual(value.metadata, {"metakey": "mounted"})

    def test_get_unmasked(self):
        value = self.store.get('test/test2')
        self.assertEqual(value.data.read(), "backing\n")
        self.assertEqual(value.metadata, {"metakey": "backing"})

    def test_get_data_masked(self):
        value = self.store.get_data('test/test1')
        self.assertEqual(value.read(), "mounted\n")

    def test_get_data_unmasked(self):
        value = self.store.get_data('test/test2')
        self.assertEqual(value.read(), "backing\n")

    def test_get_metadata_masked(self):
        value = self.store.get_metadata('test/test1')
        self.assertEqual(value, {"metakey": "mounted"})

    def test_get_metadata_unmasked(self):
        value = self.store.get_metadata('test/test2')
        self.assertEqual(value, {"metakey": "backing"})

    def test_set_masked(self):
        self.store.set('test/test2', StringValue('mounted\n', {'metakey': 'mounted'}))
        # test value in combined store
        value = self.store.get('test/test2')
        self.assertEqual(value.data.read(), "mounted\n")
        self.assertEqual(value.metadata, {"metakey": "mounted"})
        # test value in underlying store
        value = self.mounted_store.get('test2')
        self.assertEqual(value.data.read(), "mounted\n")
        self.assertEqual(value.metadata, {"metakey": "mounted"})

    def test_set_data_masked(self):
        self.store.set_data('test/test2', StringValue('mounted\n').data)
        # test value in combined store
        value = self.store.get('test/test2')
        self.assertEqual(value.data.read(), "mounted\n")
        self.assertEqual(value.metadata, {"metakey": "backing"})
        # test value in underlying store
        value = self.mounted_store.get('test2')
        self.assertEqual(value.data.read(), "mounted\n")
        self.assertEqual(value.metadata, {"metakey": "backing"})

    def test_set_metadata_masked(self):
        self.store.set_metadata('test/test2', {'metakey': 'mounted'})
        # test value in combined store
        value = self.store.get('test/test2')
        self.assertEqual(value.data.read(), "backing\n")
        self.assertEqual(value.metadata, {"metakey": "mounted"})
        # test value in underlying store
        value = self.mounted_store.get('test2')
        self.assertEqual(value.data.read(), "backing\n")
        self.assertEqual(value.metadata, {"metakey": "mounted"})

    def test_update_metadata_masked_1(self):
        self.store.update_metadata('test/test2', {'metakey': 'mounted'})
        # test value in combined store
        value = self.store.get('test/test2')
        self.assertEqual(value.data.read(), "backing\n")
        self.assertEqual(value.metadata, {"metakey": "mounted"})
        # test value in underlying store
        value = self.mounted_store.get('test2')
        self.assertEqual(value.data.read(), "backing\n")
        self.assertEqual(value.metadata, {"metakey": "mounted"})

    def test_update_metadata_masked_2(self):
        self.store.update_metadata('test/test2', {'newkey': 'mounted'})
        # test value in combined store
        value = self.store.get('test/test2')
        self.assertEqual(value.data.read(), "backing\n")
        self.assertEqual(value.metadata, {"metakey": "backing", 'newkey': "mounted"})
        # test value in underlying store
        value = self.mounted_store.get('test2')
        self.assertEqual(value.data.read(), "backing\n")
        self.assertEqual(value.metadata, {"metakey": "backing", 'newkey': "mounted"})

    def test_push(self):
        self.store.push('test/test1')
        # test value in combined store
        value = self.store.get('test/test1')
        self.assertEqual(value.data.read(), "mounted\n")
        self.assertEqual(value.metadata, {"metakey": "mounted"})
        # check that it is missing in mounted_store
        self.assertFalse(self.mounted_store.exists('test1'))
        # test value in backing store
        value = self.backing_store.get('test/test1')
        self.assertEqual(value.data.read(), "mounted\n")
        self.assertEqual(value.metadata, {"metakey": "mounted"})


class MountedStoreReadTest(abstract_test.AbstractStoreReadTest):

    def setUp(self):
        """ Set up a data store for the test case

        The store should have:

            * a key 'test1' with a file-like data object containing the
              bytes 'test2\n' and metadata {'a_str': 'test3', 'an_int': 1,
              'a_float': 2.0, 'a_bool': True, 'a_list': ['one', 'two', 'three'],
              'a_dict': {'one': 1, 'two': 2, 'three': 3}}

            * keys 'key0' through 'key9' with values 'value0' through 'value9'
              in filelike objects, and metadata {'query_test1': 'value',
              'query_test2': 0 through 9, 'optional': True for even,
              not present for odd}

        and set into 'self.store'.
        """
        super(MountedStoreReadTest, self).setUp()
        self.mounted_store = DictMemoryStore()
        self.backing_store = DictMemoryStore()
        t = time.time()
        self.backing_store._store['test1'] = (
            'test2\n',
            {
                'a_str': 'test3',
                'an_int': 1,
                'a_float': 2.0,
                'a_bool': True,
                'a_list': ['one', 'two', 'three'],
                'a_dict': {'one': 1, 'two': 2, 'three': 3}
            }, t, t
        )
        stores = [self.mounted_store, self.backing_store]
        for i in range(10):
            metadata = {'query_test1': 'value',
                'query_test2': i}
            if i % 2 == 0:
                metadata['optional'] = True
            t = time.time()
            stores[i%2]._store['key%d'%i] = ('value%d' % i, metadata, t, t)
        self.store = MountedStore('', self.mounted_store, self.backing_store)

    #def utils_large(self):
    #    self.store2.from_bytes('test3', '')#'test4'*10000000)

class MountedStoreWriteTest(abstract_test.AbstractStoreWriteTest):

    def setUp(self):
        """ Set up a data store for the test case

        The store should have:

            * a key 'test1' with a file-like data object containing the
              bytes 'test2\n' and metadata {'a_str': 'test3', 'an_int': 1,
              'a_float': 2.0, 'a_bool': True, 'a_list': ['one', 'two', 'three'],
              'a_dict': {'one': 1, 'two': 2, 'three': 3}}

            * a series of keys 'existing_key0' through 'existing_key9' with
              data containing 'existing_value0' throigh 'existing_value9' and
              metadata {'meta': True, 'meta1': 0} through {'meta': True, 'meta1': -9}

        and set into 'self.store'.
        """
        super(MountedStoreWriteTest, self).setUp()
        self.mounted_store = DictMemoryStore()
        self.backing_store = DictMemoryStore()
        t = time.time()
        self.backing_store._store['test1'] = (
            'test2\n',
            {
                'a_str': 'test3',
                'an_int': 1,
                'a_float': 2.0,
                'a_bool': True,
                'a_list': ['one', 'two', 'three'],
                'a_dict': {'one': 1, 'two': 2, 'three': 3}
            }, t, t
        )
        stores = [self.mounted_store, self.backing_store]
        for i in range(10):
            key = 'existing_key'+str(i)
            data = 'existing_value'+str(i)
            metadata = {'meta': True, 'meta1': -i}
            t = time.time()
            stores[i%2]._store[key] = (data, metadata, t, t)
        self.store = MountedStore('', self.mounted_store, self.backing_store)

    def test_multiset_metadata(self):
        super(MountedStoreWriteTest, self).test_multiset_metadata()
        keys = ['existing_key'+str(i) for i in range(10)]
        metadatas = [{'meta1': i, 'meta2': True} for i in range(10)]
        for i in range(10):
            self.assertTrue(self.mounted_store.exists(keys[i]))
            self.assertEquals(self.mounted_store.get_metadata(keys[i]), metadatas[i])

    def test_delete(self):
        """ Test that delete works for keys in mounted store """
        t = time.time()
        self.mounted_store._store['test2'] = (
            'test2\n', {}, t, t
        )
        self.store.delete('test2')
        self.assertFalse(self.store.exists('test2'))

    """
    def test_set(self):
        super(DictMemoryStoreWriteTest, self).test_set()
        self.assertEqual(self.store._data['test3'], 'test4')
        self.assertEqual(self.store._metadata['test3'], {
            'a_str': 'test5',
            'an_int': 2,
            'a_float_1': 3.0,
            'a_bool_1': True,
            'a_list_1': ['one', 'two', 'three'],
            'a_dict_1': {'one': 1, 'two': 2, 'three': 3}
        })

    def test_set_copies(self):
        super(DictMemoryStoreWriteTest, self).test_set_copies()
        self.assertEqual(self.store._metadata['test3'], {
            'a_str': 'test5',
            'an_int': 2,
            'a_float_1': 3.0,
            'a_bool_1': True,
            'a_list_1': ['one', 'two', 'three'],
            'a_dict_1': {'one': 1, 'two': 2, 'three': 3}
        })

    def test_set_large(self):
        super(DictMemoryStoreWriteTest, self).test_set_large()
        self.assertEqual(self.store._data['test3'], 'test4'*10000000)
        self.assertEqual(self.store._metadata['test3'], {
            'a_str': 'test5',
            'an_int': 2,
            'a_float_1': 3.0,
            'a_bool_1': True,
            'a_list_1': ['one', 'two', 'three'],
            'a_dict_1': {'one': 1, 'two': 2, 'three': 3}
        })

    def test_set_buffer(self):
        super(DictMemoryStoreWriteTest, self).test_set_buffer()
        self.assertEqual(self.store._data['test3'], 'test4'*8000)
        self.assertEqual(self.store._metadata['test3'], {
            'a_str': 'test5',
            'an_int': 2,
            'a_float_1': 3.0,
            'a_bool_1': True,
            'a_list_1': ['one', 'two', 'three'],
            'a_dict_1': {'one': 1, 'two': 2, 'three': 3}
        })

    def test_set_data(self):
        super(DictMemoryStoreWriteTest, self).test_set_data()
        self.assertEqual(self.store._data['test1'], 'test4')

    def test_set_data_large(self):
        super(DictMemoryStoreWriteTest, self).test_set_data_large()
        self.assertEqual(self.store._data['test3'], 'test4'*10000000)

    def test_set_data_buffer(self):
        super(DictMemoryStoreWriteTest, self).test_set_data_buffer()
        self.assertEqual(self.store._data['test1'], 'test4'*8000)

    def test_set_metadata(self):
        super(DictMemoryStoreWriteTest, self).test_set_metadata()
        self.assertEqual(self.store._metadata['test1'], {
            'a_str': 'test5',
            'an_int': 2,
            'a_float_1': 3.0,
            'a_bool_1': True,
            'a_list_1': ['one', 'two', 'three'],
            'a_dict_1': {'one': 1, 'two': 2, 'three': 3}
        })

    def test_update_metadata(self):
        super(DictMemoryStoreWriteTest, self).test_update_metadata()
        self.assertEqual(self.store._metadata['test1'], {
            'a_float': 2.0,
            'a_list': ['one', 'two', 'three'],
            'a_dict': {'one': 1, 'two': 2, 'three': 3},
            'a_str': 'test5',
            'a_bool': True,
            'an_int': 2,
            'a_float_1': 3.0,
            'a_bool_1': True,
            'a_list_1': ['one', 'two', 'three'],
            'a_dict_1': {'one': 1, 'two': 2, 'three': 3}
        })

    def test_delete(self):
        super(DictMemoryStoreWriteTest, self).test_delete()
        self.assertFalse('test1' in self.store._data)
        self.assertFalse('test1' in self.store._metadata)

    def test_multiset(self):
        super(DictMemoryStoreWriteTest, self).test_multiset()
        keys = ['set_key'+str(i) for i in range(10)]
        values = ['set_value'+str(i) for i in range(10)]
        metadatas = [{'meta1': i, 'meta2': True} for i in range(10)]
        for i in range(10):
            self.assertEquals(self.store._data[keys[i]], values[i])
            self.assertEquals(self.store._metadata[keys[i]], metadatas[i])

    def test_multiset_overwrite(self):
        super(DictMemoryStoreWriteTest, self).test_multiset_overwrite()
        keys = ['existing_key'+str(i) for i in range(10)]
        values = ['set_value'+str(i) for i in range(10)]
        metadatas = [{'meta1': i, 'meta2': True} for i in range(10)]
        for i in range(10):
            self.assertEquals(self.store._data[keys[i]], values[i])
            self.assertEquals(self.store._metadata[keys[i]], metadatas[i])

    def test_multiset_data(self):
        super(DictMemoryStoreWriteTest, self).test_multiset_data()
        keys = ['existing_key'+str(i) for i in range(10)]
        values = ['set_value'+str(i) for i in range(10)]
        for i in range(10):
            self.assertEquals(self.store._data[keys[i]], values[i])

    def test_multiset_metadata(self):
        super(DictMemoryStoreWriteTest, self).test_multiset_metadata()
        keys = ['existing_key'+str(i) for i in range(10)]
        metadatas = [{'meta1': i, 'meta2': True} for i in range(10)]
        for i in range(10):
            self.assertEquals(self.store._metadata[keys[i]], metadatas[i])

    def test_multiupdate_metadata(self):
        super(DictMemoryStoreWriteTest, self).test_multiupdate_metadata()
        keys = ['existing_key'+str(i) for i in range(10)]
        metadatas = [{'meta1': i, 'meta2': True} for i in range(10)]
        for i in range(10):
            expected = {'meta': True}
            expected.update(metadatas[i])
            self.assertEquals(self.store._metadata[keys[i]], metadatas[i])

    def test_from_file(self):
        super(DictMemoryStoreWriteTest, self).test_from_file()
        self.assertEqual(self.store._data['test3'], 'test4')

    def test_from_file_large(self):
        super(DictMemoryStoreWriteTest, self).test_from_file_large()
        self.assertEqual(self.store._data['test3'], 'test4'*10000000)

    def test_from_bytes(self):
        super(DictMemoryStoreWriteTest, self).test_from_bytes()
        self.assertEqual(self.store._data['test3'], 'test4')
    """
