import sys
import shutil

if len(sys.argv) != 2:
    sys.exit('Usage: set_target_temp.py <temp/off>')

if sys.argv[1].lower() == 'off':
    temp = 'off'
else:
    temp = float(sys.argv[1])
    assert 45 <= temp <= 80, 'Target temp out of range [45, 80]: %g' % temp

with open('.tmp', 'w') as out:
    out.write(str(temp))

shutil.move('.tmp', '.target_temp')

print 'Temperature successfully set to', temp
