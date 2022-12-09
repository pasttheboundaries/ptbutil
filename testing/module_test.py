from ptbutil.testing import test_function
from ptbutil import debug
from ptbutil.meta import spar

@test_function
def test_debug_module():
    @debug.FuncPooler
    def a():
        return 'a'

    @debug.FuncPooler
    def b():
        return 'b'

    @debug.FuncPooler
    def c():
        return 'c'

    for _ in range(100):
        pooled_list = [func() for func in debug.FuncPooler.random_pool(3)]
        pooled = ''.join(pooled_list)
        assert  pooled in ('aaa','aab','aac',
                           'aba','abb','abc',
                           'aca','acb','acc',
                           'baa','bab','bac',
                           'bba','bbb','bbc',
                           'bca','bcb','bcc',
                           'caa', 'cab', 'cac',
                           'cba', 'cbb', 'cbc',
                           'cca', 'ccb', 'ccc')

    debug.FuncPooler.purge()
    assert len(debug.FuncPooler.cache) == 0

@test_function
def test_meta_module():
    def a(a, b, c=None, **kwargs):
        pass
    assert spar(a) == ('a', 'b', 'c', 'kwargs')


if __name__ == '__main__':
    test_debug_module()
    test_meta_module()
