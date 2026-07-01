⍝ Salary analysis: calculate average and max
⍝ Expected: Avg salary and max salary
Salaries ← 50000 60000 75000 55000 80000
AvgSalary ← (+/Salaries) ÷ ⍴Salaries
MaxSalary ← ⌈/Salaries
MinSalary ← ⌊/Salaries
AvgSalary, MaxSalary, MinSalary
