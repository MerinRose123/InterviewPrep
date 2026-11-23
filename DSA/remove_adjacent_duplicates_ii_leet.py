"""
1209. Remove All Adjacent Duplicates in String II

Given a string s and a positive integer k, repeatedly delete k adjacent
identical characters until no deletions are possible. After each deletion,
the characters on either side become adjacent. Return the final string.

Input: s = "deeedbbcccbdaa", k = 3
Output: "aa"
"""


class Node:
    def __init__(self, value="", next=None):
        self.value = value
        self.next = next


class Stack:
    def __init__(self):
        self.head = Node()

    def push(self, elem):
        self.head.next = Node(elem, self.head.next)

    def pop(self):
        node = self.head.next
        if node is None:
            return None
        self.head.next = node.next
        return node.value

    def peek(self):
        return self.head.next.value if self.head.next else None

    def is_empty(self):
        return self.head.next is None


def get_result(s, k):
    stack = Stack()
    for elem in s:
        top = stack.peek()
        count = top[1] + 1 if top and top[0] == elem else 1
        stack.push((elem, count))

        if count == k:
            for _ in range(k):
                stack.pop()

    result = []
    while not stack.is_empty():
        result.append(stack.pop()[0])
    return "".join(reversed(result))


if __name__ == "__main__":
    print(get_result("deeedbbcccbdaa", 3))
    print(get_result("abcd", 2))
