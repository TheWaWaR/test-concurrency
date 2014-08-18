=begin
results/07-03_17:46:57_summary.json

test_http.go 0.34%
test_martini.go 0.23%
test_tornado.py 0.23%
test_webpy_gevent.py 0.21%
=end

require 'json'

json_result = JSON.parse(File.read('results/07-03_17:46:57_summary.json'))

h = Hash.new()

total = 0
for test in json_result['tests']
	sum = 0
	for result in test['results']
		sum += result['transaction-rate(trans/sec)_TOTAL']
	end

	h[test['app']] = sum
	total += sum
end

for k, v in h 
	puts "%s %.2f\%" % [k, v/total]
end