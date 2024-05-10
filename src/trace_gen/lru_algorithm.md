
# LRU 2C-array Algorithm

The Least Recently Used (LRU) 2C-array algorithm is an efficient method for implementing a cache eviction policy using a fixed-size array. This algorithm is particularly suitable for scenarios where memory constraints prevent the use of linked lists.

## Algorithm Overview
```plaintext

/*
  +-+-+-+-+-+-+-+-+-+-+-+-+-+
  | | |x| |x| |x| | | | | | |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+
   0   ^         ^
	   |         head ->
	   tail ->
  head points to first unoccupied entry
  tail may point to empty entry
 */
```
- Instead of using a linked list, the algorithm keeps an array A of size 2C, where C represents the cache size. 
- Array A stores items (e.g. pointers) in the cache and NULL values to indicate empty slots.
- Keeps a hash table H to store integer indexes of the items in A.
- `head` points to the first unoccupied entry in A, and `tail` points to the oldest item in A, might be NULL.

## Operations

### Insert (Item Not in Cache):

```plaintext
Initialize head = tail = 0

Insert (i.e. item not in cache):
    A[head] = item
    H[item] = head
    head++

Evict (if |A!=NULL| == C, do before inserting):
    while A[tail] == NULL
        tail++
    item = A[tail]
    delete H[item]
    A[tail++] = NULL

Access (item already in cache):
    i = H[item]
    A[i] = NULL
    insert(item)

If (`head' reaches the end of A):
    copy all non-null items to the bottom of A
    now tail == 0
        head <= C
```
