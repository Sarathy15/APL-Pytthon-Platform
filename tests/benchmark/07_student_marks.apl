⍝ Student marks analysis
⍝ Expected: Average, max, and min marks
Marks ← 85 90 78 92 88 75 95 89
AvgMarks ← (+/Marks) ÷ ⍴Marks
MaxMarks ← ⌈/Marks
MinMarks ← ⌊/Marks
PassCount ← +/(Marks ≥ 80)
AvgMarks, MaxMarks, MinMarks, PassCount
