from django.core.management.base import BaseCommand
from learning.models import Concept, Question
import random
# Authored starter content: works without an external AI service.
BANK = [
('Arrays','Array access by index usually takes what time?','O(1)','O(n)','O(n²)','O(log n)'),
('Arrays','Inserting at the front of a packed array requires what?','Shifting elements','Sorting all keys','No movement','Creating a tree'),
('Linked List','What links nodes in a singly linked list?','Next pointers','Only numeric indices','Heap priorities','Hash codes'),
('Linked List','Searching an unsorted linked list usually takes what time?','O(n)','O(1)','O(log n)','O(n²)'),
('Stack','Which ordering rule does a stack follow?','LIFO','FIFO','Smallest first','Random'),
('Stack','Which operation removes the top item?','Pop','Enqueue','Hash','Sort'),
('Queue','Which ordering rule does a queue follow?','FIFO','LIFO','Largest first','Random'),
('Queue','Which operation adds to a queue?','Enqueue','Pop','Rotate','Hash'),
('Hash Table','What is a hash collision?','Keys map to the same bucket','A key is deleted','An array is sorted','A queue is full'),
('Hash Table','With a good hash and controlled load, average lookup is usually what?','O(1)','O(n²)','O(n log n)','O(2ⁿ)'),
('Binary Tree','A binary-tree node has at most how many children?','2','1','3','Unlimited'),
('Binary Tree','Left subtree, node, right subtree is which traversal?','Inorder','Preorder','Postorder','Level order'),
('BST','In a BST with distinct keys, left subtree keys are what?','Smaller than the node key','Larger than the node key','All equal','Unordered'),
('Heap','The root of a min-heap contains what?','The smallest key','The largest key','Always the median','Always the newest key'),
('Graph','An edge represents what?','A connection between vertices','An array index','A stack operation','A sorted key'),
('Trie','Which task suits a trie?','Prefix lookup','Matrix multiplication','Heap balancing','In-place integer sorting'),
('BFS','Breadth-first search typically uses what?','A queue','Only a stack','A binary heap always','A sorting network'),
('DFS','Iterative depth-first search can use what?','A stack','A queue only','A priority queue always','A sorted array only'),
('Recursion','What stops recursive calls?','A reachable base case','Always larger input','A sorting step','A hash collision'),
('Searching','Binary search requires what?','Sorted searchable order','Random order','Unique keys always','A linked list only'),
('Sorting','Which is a comparison-based sorting algorithm?','Merge sort','BFS','Dijkstra','Hash lookup'),
('Greedy','A greedy algorithm chooses what at each step?','A locally best available choice','Every solution','A random answer','Only recursive calls'),
('Dynamic Prog','Dynamic programming reuses what?','Overlapping subproblem results','Only random values','Unrelated problems','No stored results'),
('Dijkstra','Standard Dijkstra requires which edge weights?','Non-negative','All negative','Only zero','Only equal'),
('KMP','What helps KMP avoid rechecking matches?','A prefix/failure table','A heap','An adjacency matrix','A random number'),
('Time Complexity','O(n) is what kind of asymptotic upper bound?','Linear','Constant','Quadratic','Exponential'),
]
class Command(BaseCommand):
    help='Add authored starter questions without overwriting existing content.'
    def handle(self,*args,**options):
        count=0
        for name,text,answer,*wrong in BANK:
            for concept in Concept.objects.filter(name=name):
                opts=[answer]+wrong;random.shuffle(opts)
                defaults=dict(zip(['option_a','option_b','option_c','option_d'],opts))
                defaults.update(correct_answer='abcd'[opts.index(answer)],difficulty='easy',ai_generated=False)
                _,created=Question.objects.get_or_create(concept=concept,question_text=text,defaults=defaults);count+=created
        self.stdout.write(f'Added {count} starter questions.')
