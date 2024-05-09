Instead of a linked list, keep an array \( A \) of size \( 2C \) (for a cache of size \( C \)) containing up to \( C \) items (e.g. pointers) and \( C \) or more NULL values, and a head and tail pointer, and have hash table \( H[item] \) store integer indexes in the range \( 0..2C-1 \).

Start with \( \text{head} = \text{tail} = 0 \)

\[
\text{Insert (i.e. item not in cache):}
\]
\[
    A[\text{head}] = \text{item}
\]
\[
    H[\text{item}] = \text{head}
\]
\[
    \text{head++}
\]

\[
\text{Evict (if } |A \neq \text{NULL}| == C, \text{ do before inserting):}
\]
\[
    \text{while } A[\text{tail}] == \text{NULL}
\]
\[
        \text{tail++}
\]
\[
    \text{item} = A[\text{tail}]
\]
\[
    \text{delete } H[\text{item}]
\]
\[
    A[\text{tail++}] = \text{NULL}
\]

\[
\text{Access (item already in cache):}
\]
\[
    i = H[\text{item}]
\]
\[
    A[i] = \text{NULL}
\]
\[
    \text{insert(item)}
\]

When \( \text{head} \) reaches the end of the array, copy all the non-null elements down to the bottom of the array. Now \( \text{tail} == 0 \) and \( \text{head} \leq C \)
