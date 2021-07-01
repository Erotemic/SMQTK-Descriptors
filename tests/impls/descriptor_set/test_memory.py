import pickle
import unittest

import numpy

from smqtk_core.dict import merge_dict
from smqtk_dataprovider.impls.data_element.memory import DataMemoryElement, BYTES_CONFIG_ENCODING
from smqtk_descriptors.impls.descriptor_element.memory import DescriptorMemoryElement
from smqtk_descriptors.impls.descriptor_set.memory import MemoryDescriptorSet


RAND_UUID = 0


def random_descriptor() -> DescriptorMemoryElement:
    global RAND_UUID
    d = DescriptorMemoryElement('random', RAND_UUID)
    d.set_vector(numpy.random.rand(64))
    RAND_UUID += 1
    return d


class TestMemoryDescriptorSet (unittest.TestCase):

    def test_is_usable(self) -> None:
        # Always usable because no dependencies.
        self.assertEqual(MemoryDescriptorSet.is_usable(), True)

    def test_default_config(self) -> None:
        # Default should be valid for constructing a new instance.
        c = MemoryDescriptorSet.get_default_config()
        self.assertEqual(MemoryDescriptorSet.from_config(c).get_config(), c)

    def test_from_config_null_cache_elem(self) -> None:
        inst = MemoryDescriptorSet.from_config({'cache_element': None})
        self.assertIsNone(inst.cache_element)
        self.assertEqual(inst._table, {})

        inst = MemoryDescriptorSet.from_config({
            'cache_element': {
                'type': None
            }
        })
        self.assertIsNone(inst.cache_element)
        self.assertEqual(inst._table, {})

    def test_from_config_null_cache_elem_type(self) -> None:
        # An empty cache should not trigger loading on construction.
        expected_empty_cache = DataMemoryElement()
        dme_key = 'smqtk_dataprovider.impls.data_element.memory.DataMemoryElement'
        inst = MemoryDescriptorSet.from_config({
            'cache_element': {
                'type': dme_key,
                dme_key: {'bytes': ''}
            }
        })
        self.assertEqual(inst.cache_element, expected_empty_cache)
        self.assertEqual(inst._table, {})

    def test_from_config(self) -> None:
        # Configured cache with some picked bytes
        # Then convert to "string" (decode -> unicode) for python version used.
        expected_table = dict(a=1, b=2, c=3)
        expected_cache = DataMemoryElement(bytes=pickle.dumps(expected_table))
        expected_cache_json_str = \
            expected_cache.get_bytes().decode(BYTES_CONFIG_ENCODING)
        dme_key = 'smqtk_dataprovider.impls.data_element.memory.DataMemoryElement'
        inst = MemoryDescriptorSet.from_config({
            'cache_element': {
                'type': dme_key,
                dme_key: {'bytes': expected_cache_json_str}
            }
        })
        self.assertEqual(inst.cache_element, expected_cache)
        self.assertEqual(inst._table, expected_table)

    def test_init_no_cache(self) -> None:
        inst = MemoryDescriptorSet()
        self.assertIsNone(inst.cache_element, None)
        self.assertEqual(inst._table, {})

    def test_init_empty_cache(self) -> None:
        cache_elem = DataMemoryElement()
        inst = MemoryDescriptorSet(cache_element=cache_elem)
        self.assertEqual(inst.cache_element, cache_elem)
        self.assertEqual(inst._table, {})

    def test_init_with_cache(self) -> None:
        d_list = (random_descriptor(), random_descriptor(),
                  random_descriptor(), random_descriptor())
        expected_table = dict((r.uuid(), r) for r in d_list)
        expected_cache = DataMemoryElement(bytes=pickle.dumps(expected_table))

        inst = MemoryDescriptorSet(expected_cache)
        self.assertEqual(len(inst._table), 4)
        self.assertEqual(inst.cache_element, expected_cache)
        self.assertEqual(inst._table, expected_table)
        self.assertEqual(set(inst._table.values()), set(d_list))

    def test_get_config(self) -> None:
        self.assertEqual(
            MemoryDescriptorSet().get_config(),
            MemoryDescriptorSet.get_default_config()
        )

        self.assertEqual(
            MemoryDescriptorSet(None).get_config(),
            MemoryDescriptorSet.get_default_config()
        )

        empty_elem = DataMemoryElement()
        dme_key = 'smqtk_dataprovider.impls.data_element.memory.DataMemoryElement'
        self.assertEqual(
            MemoryDescriptorSet(empty_elem).get_config(),
            merge_dict(MemoryDescriptorSet.get_default_config(), {
                'cache_element': {'type': dme_key}
            })
        )

        dict_pickle_bytes = pickle.dumps({1: 1, 2: 2, 3: 3}, -1)
        dict_pickle_bytes_str = dict_pickle_bytes.decode(BYTES_CONFIG_ENCODING)
        cache_elem = DataMemoryElement(bytes=dict_pickle_bytes)
        self.assertEqual(
            MemoryDescriptorSet(cache_elem).get_config(),
            merge_dict(MemoryDescriptorSet.get_default_config(), {
                'cache_element': {
                    dme_key: {
                        'bytes': dict_pickle_bytes_str
                    },
                    'type': dme_key
                }
            })
        )

    def test_cache_table_no_cache(self) -> None:
        inst = MemoryDescriptorSet()
        inst._table = {}
        inst.cache_table()  # should basically do nothing
        self.assertIsNone(inst.cache_element)

    def test_cache_table_empty_table(self) -> None:
        inst = MemoryDescriptorSet(DataMemoryElement(), -1)
        inst._table = {}
        expected_table_pickle_bytes = pickle.dumps(inst._table, -1)

        inst.cache_table()
        assert inst.cache_element is not None
        self.assertEqual(inst.cache_element.get_bytes(),
                         expected_table_pickle_bytes)

    def test_add_descriptor(self) -> None:
        index = MemoryDescriptorSet()

        d1 = random_descriptor()
        index.add_descriptor(d1)
        self.assertEqual(index._table[d1.uuid()], d1)

        d2 = random_descriptor()
        index.add_descriptor(d2)
        self.assertEqual(index._table[d2.uuid()], d2)

    def test_add_many(self) -> None:
        descrs = [
            random_descriptor(),
            random_descriptor(),
            random_descriptor(),
            random_descriptor(),
            random_descriptor(),
        ]
        index = MemoryDescriptorSet()
        index.add_many_descriptors(descrs)

        # Compare code keys of input to code keys in internal table
        self.assertEqual(set(index._table.keys()),
                         set([e.uuid() for e in descrs]))

        # Get the set of descriptors in the internal table and compare it with
        # the set of generated random descriptors.
        r_set = set(index._table.values())
        self.assertEqual(
            set([e for e in descrs]),
            r_set
        )

    def test_count(self) -> None:
        index = MemoryDescriptorSet()
        self.assertEqual(index.count(), 0)

        d1 = random_descriptor()
        index.add_descriptor(d1)
        self.assertEqual(index.count(), 1)

        d2, d3, d4 = (random_descriptor(),
                      random_descriptor(),
                      random_descriptor())
        index.add_many_descriptors([d2, d3, d4])
        self.assertEqual(index.count(), 4)

        d5 = random_descriptor()
        index.add_descriptor(d5)
        self.assertEqual(index.count(), 5)

    def test_get_descriptors(self) -> None:
        descrs = [
            random_descriptor(),   # [0]
            random_descriptor(),   # [1]
            random_descriptor(),   # [2]
            random_descriptor(),   # [3]
            random_descriptor(),   # [4]
        ]
        index = MemoryDescriptorSet()
        index.add_many_descriptors(descrs)

        # single descriptor reference
        r = index.get_descriptor(descrs[1].uuid())
        self.assertEqual(r, descrs[1])

    def test_get_many_descriptor(self) -> None:
        descrs = [
            random_descriptor(),  # [0]
            random_descriptor(),  # [1]
            random_descriptor(),  # [2]
            random_descriptor(),  # [3]
            random_descriptor(),  # [4]
        ]
        index = MemoryDescriptorSet()
        index.add_many_descriptors(descrs)

        # multiple descriptor reference
        r = list(index.get_many_descriptors([descrs[0].uuid(),
                                             descrs[3].uuid()]))
        self.assertEqual(len(r), 2)
        self.assertEqual(set(r),
                         {descrs[0], descrs[3]})

    def test_clear(self) -> None:
        i = MemoryDescriptorSet()
        n = 10

        descrs = [random_descriptor() for _ in range(n)]
        i.add_many_descriptors(descrs)
        self.assertEqual(len(i), n)
        i.clear()
        self.assertEqual(len(i), 0)
        self.assertEqual(i._table, {})

    def test_has(self) -> None:
        i = MemoryDescriptorSet()
        descrs = [random_descriptor() for _ in range(10)]
        i.add_many_descriptors(descrs)

        self.assertTrue(i.has_descriptor(descrs[4].uuid()))
        self.assertFalse(i.has_descriptor('not_an_int'))

    def test_added_descriptor_table_caching(self) -> None:
        cache_elem = DataMemoryElement(readonly=False)
        descrs = [random_descriptor() for _ in range(3)]
        expected_table = dict((r.uuid(), r) for r in descrs)

        i = MemoryDescriptorSet(cache_elem)
        assert i.cache_element is not None
        self.assertTrue(cache_elem.is_empty())

        # Should add descriptors to table, caching to writable element.
        i.add_many_descriptors(descrs)
        self.assertFalse(cache_elem.is_empty())
        self.assertEqual(pickle.loads(i.cache_element.get_bytes()),
                         expected_table)

        # Changing the internal table (remove, add) it should reflect in
        # cache
        new_d = random_descriptor()
        expected_table[new_d.uuid()] = new_d
        i.add_descriptor(new_d)
        self.assertEqual(pickle.loads(i.cache_element.get_bytes()),
                         expected_table)

        rm_d = list(expected_table.values())[0]
        del expected_table[rm_d.uuid()]
        i.remove_descriptor(rm_d.uuid())
        self.assertEqual(pickle.loads(i.cache_element.get_bytes()),
                         expected_table)

    def test_remove(self) -> None:
        i = MemoryDescriptorSet()
        descrs = [random_descriptor() for _ in range(100)]
        i.add_many_descriptors(descrs)
        self.assertEqual(len(i), 100)
        self.assertEqual(list(i.descriptors()), descrs)

        # remove singles
        i.remove_descriptor(descrs[0].uuid())
        self.assertEqual(len(i), 99)
        self.assertEqual(set(i.descriptors()),
                         set(descrs[1:]))

        # remove many
        rm_d = descrs[slice(45, 80, 3)]
        i.remove_many_descriptors((d.uuid() for d in rm_d))
        self.assertEqual(len(i), 99 - len(rm_d))
        self.assertEqual(set(i.descriptors()),
                         set(descrs[1:]).difference(rm_d))

    def test_natural_iter(self) -> None:
        """Test that iterating over the descriptor set appropriately
        yields the descriptor element contents."""
        i = MemoryDescriptorSet()
        descrs = [random_descriptor() for _ in range(100)]
        i.add_many_descriptors(descrs)
        self.assertEqual(set(i),
                         set(descrs))

    def test_descrs(self) -> None:
        i = MemoryDescriptorSet()
        descrs = [random_descriptor() for _ in range(100)]
        i.add_many_descriptors(descrs)
        self.assertEqual(set(i.descriptors()),
                         set(descrs))

    def test_keys(self) -> None:
        i = MemoryDescriptorSet()
        descrs = [random_descriptor() for _ in range(100)]
        i.add_many_descriptors(descrs)
        self.assertEqual(set(i.keys()),
                         set(d.uuid() for d in descrs))

    def test_items(self) -> None:
        i = MemoryDescriptorSet()
        descrs = [random_descriptor() for _ in range(100)]
        i.add_many_descriptors(descrs)
        self.assertEqual(set(i.items()),
                         set((d.uuid(), d) for d in descrs))
