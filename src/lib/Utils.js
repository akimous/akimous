// https://stackoverflow.com/questions/22697936/binary-search-in-javascript
function binarySearch(array, target) {
    let lo = -1,
        hi = array.length
    while (1 + lo !== hi) {
        const mi = lo + ((hi - lo) >> 1);
        if (array[mi].name >= target) hi = mi;
        else lo = mi
    }
    return hi;
}

export {
    binarySearch
}
