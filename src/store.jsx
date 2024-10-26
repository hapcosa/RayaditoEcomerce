import {legacy_createStore, applyMiddleware } from "redux";
import thunk from "redux-thunk";
import { persistStore, persistReducer } from 'redux-persist'
import rootReducers from './redux/reducers';
import storage from 'redux-persist/lib/storage';
import { composeWithDevTools } from 'redux-devtools-extension';

const persistConfig = {
    key: 'root',
    storage,
    blacklist: ['rootReducers.Payment', 'Alert']

  }


const initialState = {};
const persistedReducer = persistReducer(persistConfig, rootReducers)
const middleware = [thunk];

export const store = legacy_createStore(persistedReducer, initialState,
    composeWithDevTools(applyMiddleware(...middleware) )
    );



export const persistor = persistStore(store)


