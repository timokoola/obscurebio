import pprint

if __name__ == '__main__':
    f = open("letter_score.txt")
    result = {}
    for l in f:
        line = l.split()
        result[line[0]] = int((1.0 / float(line[3])) * 1000.0)
    f.close()
    print result
