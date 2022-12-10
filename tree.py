import pickle
import json
from ptbutil.iteration import merge_2_dicts

# class Tree:
#     """
#     This is idea only. It is not suitable for use.
#     The purpose of this class is to keep idea of a tree structure
#     BUT
#     where there is a branch there can not be leaf
#     SO it only keeps leaves at the end of the branch
#     If a leaf is exendend into a branch its value disappears
#     """
#     def __init__(self, args):
#         self._tree = dict()
#         self._distribute_args(self._tree, args)
#
#     def _distribute_args(self, _tree, args, write=True):
#         if len(args) > 1:
#             key, *val = args
#             if key in _tree:
#                 if isinstance(_tree[key], dict):
#                     return self._distribute_args(_tree[key], val, write=write)
#                 elif _tree[key] is True:
#                     _tree[key] = dict()
#                     return self._distribute_args(_tree[key], val, write=write)
#                 else:
#                     raise RuntimeError('error in Tree')
#
#
#             else:
#                 if write:
#                     _tree[key] = dict()
#                     return self._distribute_args(_tree[key], val, write=write)
#                 else:
#                     return False
#         elif len(args) == 1:
#             key = args[0]
#             if key in _tree:
#                 if write:
#                     if isinstance(_tree[key], dict):
#                         return _tree[key]
#                     if _tree[key] is True:
#                         return True
#                 else:
#                     if isinstance(_tree[key], dict):
#                         return False
#                     if _tree[key] is True:
#                         return True
#             else:
#                 if write:
#                     if isinstance(_tree[key], dict):
#                         _tree[key][0] # ????
#                     if _tree[key] is True:
#                         return True
#                 else:
#                     if isinstance(_tree[key], dict):
#                         return False
#                     if _tree[key] is True:
#                         return True
#         else:  # 0
#             return self._tree
#
#     def next(self, args):
#         next_ = self._distribute_args(self._tree, args, write=False)
#         if next_ is False:
#             return False
#         elif isinstance(next_, dict):
#             return tuple(next_.keys())
#         else:
#             return
#
#     @staticmethod
#     def _search_leaves(tree):
#         current_level_leaves = []
#         for key, value in tree.items():
#             if value is True:
#                 current_level_leaves.append(key)
#             if isinstance(value, dict):
#                 current_level_leaves.extend(Tree._search_leaves(value))
#         return current_level_leaves
#
#     @staticmethod
#     def _yield_branches(tree):
#         keys = tree.keys()
#         for key in keys:
#             if isinstance(tree[key], dict):
#                 further_branches = Tree._yield_branches(tree[key])
#                 for f_branch in further_branches:
#                     current_branch = [key]
#                     current_branch.extend(f_branch)
#                     yield current_branch
#             elif tree[key] is True:
#                 yield [key]
#             else:
#                 raise RuntimeError('Iduno')
#
#     def leaves(self, args):
#         branch = self._distribute_args(self._tree, args)
#         return self._search_leaves(branch)
#
#     def branches(self):
#         brans = Tree._yield_branches(self._tree)
#         for branch in brans:
#             yield branch
#
#     def root(self):
#         return self.next('')
#
#     def to_dict(self):
#         return self._tree
#
#     def __call__(self, args, write=True):
#         return self._distribute_args(self._tree, args, write=write)
#
#     def __repr__(self):
#         return self._tree.__repr__()


class StringTree:
    """Nested dictionary holding a target value for a key which is an iterable, as a leaf under target_key.
    instantiation parameters:
    - target_key: any immutable, defaault is '00',
    - count_on_load: bool - counting leaves in big trees takes time
    methods:
    - record (key: str, value: any type): records a word into the dictionary
    splitting it letter by letter as the keys of the nested dictionary.
    - read (key: str): retrieves a value from the dictionary.
    - from_pickle(path: str): loads a dictionary from pickled file.
    - to_pickle(path: str): saves the dictionary into a pickle file.
    """
    def __init__(self, target_key='00', count_on_load=False):
        self.tree = dict()
        self.target_key = target_key
        self.n_leaves = 0
        self.counted = False
        self.count_on_load = count_on_load
        if type(self.target_key) != str or len(self.target_key) < 2:
            print("! WARNING ! : target key must be type str and is not supposed to be "
                  "a single character as it might impinge the tree!")

    def count_leaves(self):
        self.n_leaves = StringTree._count_leaves(self.tree, self.target_key)
        self.counted = True
        return self.n_leaves

    @staticmethod
    def _count_leaves(dic, leaf_key):
        count = 0
        if leaf_key in dic:
            count += 1
        for key in (k for k in dic.keys() if k != leaf_key):
            other_dic = dic[key]
            count = count + StringTree._count_leaves(other_dic, leaf_key)
        return count

    def record(self, key: any, value):
        try:
            any(key)
        except TypeError:
            raise TypeError(f'Key is to be iterable. Passed type: {str(type(key))}')
        self.counted = False
        return self._process_recording(self.tree, key, value)

    def _process_recording(self, dictionary, key_part, value):
        local_key = key_part[0]
        if len(key_part) == 1:
            if local_key in dictionary:
                if self.target_key in dictionary[local_key]:
                    old_value = dictionary[local_key][self.target_key]
                    if old_value == {value}:
                        return True # already in tree
                    else:
                        dictionary[local_key].update({
                            self.target_key: old_value.union({value})})
                    return True # added to existing record
                else:
                    dictionary[local_key].update({self.target_key: {value}})
                    return True # recorded correctly next to further branches
            else:
                dictionary.update({local_key: {self.target_key: {value}}})
                return True # recorded correctly as a first/sole branch
        else:
            if local_key in dictionary:
                subdictionary = dictionary[local_key]
                key_part = key_part[1:]
                return self._process_recording(subdictionary, key_part, value)
            else:
                dictionary.update({local_key: dict()})
                subdictionary = dictionary[local_key]
                key_part = key_part[1:]
                return self._process_recording(subdictionary, key_part, value)

    def read(self, key):
        return self._process_read(self.tree, key)

    def _process_read(self, dictionary, key_part):
        local_key = key_part[0]
        if len(key_part) == 1:
            if local_key in dictionary:
                if self.target_key in dictionary[local_key]:
                    return dictionary[local_key][self.target_key]
                else:
                    return None
            else:
                return None

        if local_key in dictionary:
            dictionary = dictionary[local_key]
            key_part = key_part[1:]
            return self._process_read(dictionary, key_part)
        else:
            return None

    def from_pickle(self, path):
        self.tree = pickle.load(open(path, 'rb'))
        if not type(self.tree) == dict:
            raise NotImplementedError('Wrong data loaded from file. Expected pickled dictionary.')
        self.count_leaves()
        return self

    def from_json(self, path):
        with open(path, 'r') as f:
            read = f.read()
        self.tree = json.loads(read)
        if not type(self.tree) == dict:
            raise NotImplementedError('Wrong data loaded from file. Expected jsonified dictionary.')
        self.count_leaves()
        return self

    def to_pickle(self, path):
        if len(path.split('.')) == 1:
            path = path+'.pickle'
        pickle.dump(self.tree, open(path, 'wb'))

    def to_json(self, path):
        with open(path, 'w') as f:
            f.write(json.dumps(self.tree))

    def __add__(self, other):
        if type(self) != type(other):
            raise TypeError('Tree class can be only added to another Tree class. Type '+str(type(other))+' passed')
        self.tree = merge_2_dicts(self.tree, other.tree)
        self.count_leaves()
        return self

    def __call__(self, key=None):
        if key:
            return self.read(key)
        else:
            return None

    def __len__(self):
        if self.counted:
            return self.n_leaves
        else:
            return self.count_leaves()
