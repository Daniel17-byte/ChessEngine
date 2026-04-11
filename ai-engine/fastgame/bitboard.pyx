# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True
# Pure C-level bitboard helpers.

cdef unsigned long long BB_RANK_1 = 0xFF
cdef unsigned long long BB_RANK_8 = 0xFF00000000000000ULL


cdef inline int popcount(unsigned long long bb) noexcept nogil:
    """Count set bits (Kernighan's method)."""
    cdef int count = 0
    while bb:
        bb &= bb - 1
        count += 1
    return count


cdef inline int lsb(unsigned long long bb) noexcept nogil:
    """Return index of lowest set bit (0-63). Undefined for bb==0."""
    cdef int idx = 0
    if bb == 0:
        return -1
    while (bb & 1) == 0:
        bb >>= 1
        idx += 1
    return idx


cdef inline void bb_to_squares(unsigned long long bb, float *plane) noexcept nogil:
    """Write 1.0 into an 8x8 flat float array for each set bit in bb."""
    cdef unsigned long long tmp = bb
    cdef int sq
    while tmp:
        sq = lsb(tmp)
        plane[sq] = 1.0
        tmp &= tmp - 1

