import { configureStore } from '@reduxjs/toolkit'
import rootReducer from './redux/reducers'

export default function configureAppStore(preloadedState) {
  const store = configureStore({
    reducer: rootReducer,
  })

  if (import.meta.env.ENV !== 'production' && module.hot) {
    module.hot.accept('./redux/reducers', () => store.replaceReducer(rootReducer))
  }

  return store
}