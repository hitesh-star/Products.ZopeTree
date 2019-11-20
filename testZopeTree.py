
"""
$Id: testZopeTree.py,v 1.2 2003/03/15 17:39:17 philipp Exp $
"""

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Testing import ZopeTestCase
from Products.ZopeTree.IZopeTree import INode, IZopeTree
from Products.ZopeTree import Node, ZopeTree

ZopeTestCase.installProduct('ZopeTree')

# simple object that can have an id an a set of children
class Item:
    def __init__(self, id, children=[]):
        self.id = id
        self.children = children

# function used to convert a set of nested tuples to items and children items.
def make_item_from_tuple(item_tuple, dict):
    children = []
    if len(item_tuple) > 1:
        for child in item_tuple[1]:
            children.append(make_item_from_tuple(child, dict))
    item = Item(item_tuple[0], children)
    dict[item_tuple[0]] = item
    return item

tree = ('a', [
           ('b', [
               ('d',), ('e',)
               ]),
           ('c', [
               ('f', [
                   ('h',), ('i',)
                   ]),
               ('g')]
           ) ]
       )

expanded_nodes = ['a', 'c']

class NodeTest(ZopeTestCase.ZopeTestCase):

    def afterSetUp(self):
        self.items = {}
        self.root_obj = make_item_from_tuple(tree, self.items)
        self.root_node = Node(self.root_obj, 0, 'id', 'children', expanded_nodes)

    def afterClear(self):
        pass

    def test_verify_interface(self):
        """Verify interface implementation"""
        from Interface.Verify import verifyObject
        self.failUnless(verifyObject(INode, self.root_node))

    def test_children(self):
        """Test children"""
        root_node = self.root_node
        # testing hasChildren()
        self.failUnless(root_node.hasChildren())
        
        # testing getChildrenNodes()
        children = [node.object for node in root_node.getChildrenNodes()]
        expected = [self.items['b'], self.items['c']]
        self.assertEqual(children, expected)

    def test_flat(self):
        """Test flat list generation"""
        root_node = self.root_node
        # testing getFlatNodes()
        children = [node.object for node in root_node.getFlatNodes()]
        # 'a' is not expected because the node on which getFlatNodes() is called
        # is not in the list
        expected = [self.items[i] for i in "bcfg"]
        self.assertEqual(children, expected)

import zlib
from StringIO import StringIO
from ZTUtils.Tree import b2a
from ZPublisher.HTTPRequest import HTTPRequest
from ZPublisher.HTTPResponse import HTTPResponse

class ZopeTreeTest(ZopeTestCase.ZopeTestCase):

    def afterSetUp(self):
        environ = os.environ.copy()
        response = HTTPResponse(stdout=StringIO())
        request = HTTPRequest(StringIO(""), environ, response)
        # emulate a cookie
        request.other['tree-expansion'] = b2a(zlib.compress(":".join(expanded_nodes)))
        self.items = {}
        self.root_obj = make_item_from_tuple(tree, self.items)
        self.tree = ZopeTree(self.root_obj, 'id', 'children', request)
        
    def afterClear(self):
        pass

    def test_verify_interface(self):
        """Verify interface implementation"""
        from Interface.Verify import verifyObject
        self.failUnless(verifyObject(IZopeTree, self.tree))

    def test_encode_tree_expansion(self):
        """Test tree expansion encoding and decoding"""
        encoded = self.tree.encodeTreeExpansion(expanded_nodes)
        decoded = self.tree.decodeTreeExpansion(encoded)
        self.assertEqual(expanded_nodes, decoded)

    def test_pre_expanded(self):
        """Test pre-expanded nodes"""
        # 'a' is not expected because the node on which getFlatNodes() is called
        # is not in the list
        expected = [self.items[i] for i in "bcfg"]
        # test against to getFlatNodes()
        flat = [node.object for node in self.tree.getFlatNodes()]
        self.assertEqual(flat, expected)

    def test_flat_dicts(self):
        """Test flat dicts"""
        flatdicts = self.tree.getFlatDicts()
        self.assertEqual(len(flatdicts), len(self.tree.getFlatNodes()))
        bdict = flatdicts[0]
        self.assertEqual(bdict['id'], 'b')
        self.failIf(bdict['expanded'])
        self.assertEqual(bdict['depth'], 1)
        self.failUnless(bdict['children'])
        self.failUnless(bdict['object'] is self.items['b'])

if __name__ == '__main__':
    framework(descriptions=1, verbosity=2)
else:
    import unittest
    def test_suite():
        suite = unittest.TestSuite()
        suite.addTest(unittest.makeSuite(NodeTest))
        suite.addTest(unittest.makeSuite(ZopeTreeTest))
        return suite
