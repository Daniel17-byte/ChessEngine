# cython: language_level=3
# Pure C-level bitboard helpers – no Python objects touched.

cdef unsigned long long BB_RANK_1
cdef unsigned long long BB_RANK_8

cdef inline int popcount(unsigned long long bb) noexcept nogil
cdef inline int lsb(unsigned long long bb) noexcept nogil
cdef inline void bb_to_squares(unsigned long long bb, float *plane) noexcept nogil

