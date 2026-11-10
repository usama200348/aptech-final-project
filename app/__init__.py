# EduPredict App Package
import os
import sys

# Ensure package root is in path
package_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(package_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
