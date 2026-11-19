"""Inspectable radix tree and collision-safe open-addressed frequency table."""
from dataclasses import dataclass, field
import re
import unicodedata


def normalize(text: str) -> str:
    clean = ''.join(c for c in unicodedata.normalize('NFKD', text.casefold()) if not unicodedata.combining(c))
    return ' '.join(re.findall(r'[^\W_]+', clean))


@dataclass
class Node:
    children: dict = field(default_factory=dict)
    values: list[int] = field(default_factory=list)


class RadixIndex:
    """Compressed prefix trie. Supports duplicate titles and prefix-of-title keys."""
    def __init__(self):
        self.root = Node()

    def insert(self, title: str, value: int):
        key = normalize(title)
        if not key:
            raise ValueError('Title must contain letters or numbers.')
        self._insert(self.root, key, value)

    def _insert(self, node, key, value):
        if not key:
            if value not in node.values:
                node.values.append(value)
            return
        for edge, child in list(node.children.items()):
            n = 0
            while n < min(len(edge), len(key)) and edge[n] == key[n]:
                n += 1
            if not n:
                continue
            if n == len(edge):
                self._insert(child, key[n:], value)
            else:
                branch = Node(children={edge[n:]: child})
                del node.children[edge]
                node.children[edge[:n]] = branch
                self._insert(branch, key[n:], value)
            return
        node.children[key] = Node(values=[value])

    def search(self, prefix: str) -> list[int]:
        key = normalize(prefix)
        node = self.root
        while key:
            for edge, child in node.children.items():
                if edge.startswith(key):
                    return self._collect(child)
                if key.startswith(edge):
                    node, key = child, key[len(edge):]
                    break
            else:
                return []
        return self._collect(node)

    def _collect(self, node):
        values = list(node.values)
        for edge in sorted(node.children):
            values.extend(self._collect(node.children[edge]))
        return values


class FrequencyTable:
    """Linear probing with resizing; collisions cannot cause an endless probe."""
    def __init__(self, capacity=16):
        self.slots = [None] * max(4, capacity)
        self.used = 0

    @staticmethod
    def hash(key):
        value = 2166136261
        for byte in key.encode('utf-8'):
            value = ((value ^ byte) * 16777619) & 0xffffffff
        return value

    def add(self, key, count=1):
        if self.used * 10 >= len(self.slots) * 7:
            old, self.slots = self.slots, [None] * (2 * len(self.slots))
            self.used = 0
            for entry in old:
                if entry:
                    self.add(*entry)
        pos = self.hash(key) % len(self.slots)
        while self.slots[pos] and self.slots[pos][0] != key:
            pos = (pos + 1) % len(self.slots)
        if self.slots[pos] is None:
            self.used += 1
            self.slots[pos] = (key, count)
        else:
            self.slots[pos] = (key, self.slots[pos][1] + count)

    def items(self):
        return sorted((s for s in self.slots if s), key=lambda x: (-x[1], x[0]))
