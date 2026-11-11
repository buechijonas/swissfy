function promisify(request) {
  return new Promise((resolve, reject) => {
    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(request.error)
  })
}

export function keyValueStore(dbName, storeName) {
  let connection = null

  function open() {
    if (!connection) {
      const request = indexedDB.open(dbName)
      request.onupgradeneeded = () => request.result.createObjectStore(storeName)
      connection = promisify(request).catch((error) => {
        connection = null
        throw error
      })
    }
    return connection
  }

  async function run(mode, action) {
    const db = await open()
    return promisify(action(db.transaction(storeName, mode).objectStore(storeName)))
  }

  return {
    get: (key) => run('readonly', (store) => store.get(key)),
    put: (key, value) => run('readwrite', (store) => store.put(value, key)),
    delete: (key) => run('readwrite', (store) => store.delete(key)),
  }
}
