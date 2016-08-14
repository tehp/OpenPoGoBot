from argparse import Namespace

from app import Kernel

test_kernel = Kernel()

config = Namespace(exclude_pludins=[])
test_kernel.import_config(config)
