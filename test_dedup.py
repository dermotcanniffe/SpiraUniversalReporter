"""Quick test to verify JUnit deduplication works."""
import sys
import os
import tempfile
import shutil

sys.path.insert(0, 'src')
from spira_integration.parsers.junit_parser import JUnitParser

# Create a temp dir with duplicated XML files (simulating surefire)
tmpdir = tempfile.mkdtemp()

xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="DemoThreeAddSubTest" tests="2" failures="1">
  <testcase name="demoThreeAddition" classname="demothreearithmetictest.DemoThreeAddSubTest" time="0.5"/>
  <testcase name="demoThreeSubtraction" classname="demothreearithmetictest.DemoThreeAddSubTest" time="0.3">
    <failure message="Expected 2 but got 1"/>
  </testcase>
</testsuite>"""

xml_content2 = """<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="DemoThreeMulDivTest" tests="1" failures="0">
  <testcase name="demoThreeMultiplication" classname="demothreearithmetictest.DemoThreeMulDivTest" time="0.2"/>
</testsuite>"""

# Simulate surefire: individual files + aggregate that contains same tests
with open(os.path.join(tmpdir, 'TEST-DemoThreeAddSubTest.xml'), 'w') as f:
    f.write(xml_content)
with open(os.path.join(tmpdir, 'TEST-DemoThreeMulDivTest.xml'), 'w') as f:
    f.write(xml_content2)

# Aggregate file with all tests (simulates testng-results.xml or merged report)
aggregate = """<?xml version="1.0" encoding="UTF-8"?>
<testsuites>
  <testsuite name="DemoThreeAddSubTest" tests="2" failures="1">
    <testcase name="demoThreeAddition" classname="demothreearithmetictest.DemoThreeAddSubTest" time="0.5"/>
    <testcase name="demoThreeSubtraction" classname="demothreearithmetictest.DemoThreeAddSubTest" time="0.3">
      <failure message="Expected 2 but got 1"/>
    </testcase>
  </testsuite>
  <testsuite name="DemoThreeMulDivTest" tests="1" failures="0">
    <testcase name="demoThreeMultiplication" classname="demothreearithmetictest.DemoThreeMulDivTest" time="0.2"/>
  </testsuite>
</testsuites>"""

with open(os.path.join(tmpdir, 'testng-results.xml'), 'w') as f:
    f.write(aggregate)

# Third copy to simulate 3x duplication (like the client's 9 results from 3 tests)
with open(os.path.join(tmpdir, 'TEST-Suite.xml'), 'w') as f:
    f.write(aggregate)

p = JUnitParser()
results = p.parse(tmpdir)
print(f"Parsed {len(results)} results (should be 3, not 9 or 12):")
for r in results:
    print(f"  {r.name} -> {r.status.value}")

assert len(results) == 3, f"Expected 3 results, got {len(results)}"
print("\n✓ Deduplication test PASSED!")

shutil.rmtree(tmpdir)
