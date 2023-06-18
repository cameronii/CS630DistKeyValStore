import paxos_hash_table

ht = paxos_hash_table.load('example.json', False)

# ht.set('key', 'value')
# ht.set('girik', 'malik')

print(ht.get('key'))
print(ht.get('girik'))
# 'value'
ht.set('key', 'v1')
print(ht.get('key'))

ht.set('val', ['1','2'])
print(ht.get('val'))

ht.lappend('val', 1,'3')
print(ht.get('val'))

ht.iset('/Users/gmalik9/Desktop/Screen Shot 2019-03-19 at 10.45.09 AM.png',['girik in london'])
print(ht.iget('/Users/gmalik9/Desktop/Screen Shot 2019-03-19 at 10.45.09 AM.png'))


ht.dump() 
# print(ht.getall())

# a=average_hash("/Users/gmalik9/Desktop/Screen Shot 2019-03-19 at 10.45.09 AM.png")
# print(a)

# import image_hash
# from PIL import Image

# hash = image_hash.average_hash(Image.open('/Users/gmalik9/Desktop/Screen Shot 2019-03-19 at 10.45.09 AM.png'))
# print(hash)