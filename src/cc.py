def __remove_local_cycle(l,i, cleaned_l):
    if i >= len(l):
        return

    if l.index(l[i]) == i:
        cleaned_l.append(l[i])
    else:
        prev_index = l.index(l[i])
        s_l = l[:prev_index]
        cleaned_l[:] = s_l + [l[i]]
    
    __remove_local_cycle(l,i+1, cleaned_l)


l = "A B C D B F H".split(" ")
cleaned = []

print(l)
print(len(l))
__remove_local_cycle(l,0,cleaned)

print(cleaned)

