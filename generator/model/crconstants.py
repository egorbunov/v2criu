TASK_STATE_UNDEF = 0x0
TASK_STATE_ALIVE = 0x1
TASK_STATE_DEAD = 0x2
TASK_STATE_STOPPED = 0x3
TASK_STATE_HELPER = 0x4
TASK_STATE_THREAD = 0x5

VMA_STATUS_AREA_REGULAR = 'VMA_AREA_REGULAR'
VMA_STATUS_FILE_PRIVATE = 'VMA_FILE_PRIVATE'
VMA_STATUS_ANON_PRIVATE = 'VMA_ANON_PRIVATE'
VMA_STATUS_FILE_SHARED = 'VMA_FILE_SHARED'
VMA_STATUS_ANON_SHARED = 'VMA_ANON_SHARED'
VMA_STATUS_AREA_VSYSCALL = 'VMA_AREA_VSYSCALL'
VMA_STATUS_AREA_VVAR = 'VMA_AREA_VVAR'
VMA_STATUS_AREA_VDSO = 'VMA_AREA_VDSO'

VMA_FLAG_MAP_PRIVATE = 'MAP_PRIVATE'
VMA_FLAG_MAP_ANON = 'MAP_ANON'
VMA_FLAG_MAP_GROWSDOWN = 'MAP_GROWSDOWN'
VMA_FLAG_MAP_SHARED = 'MAP_SHARED'

FILE_WRONLY_FLAG = 0x1
FILE_RDONLY_FLAG = 0x0