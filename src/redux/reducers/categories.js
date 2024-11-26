
import {
    GET_CATEGORIES_FAIL,
    GET_CATEGORIES_SUCCESS,
    GET_CATEGORIES_PIEDRAS_FAIL,
    GET_CATEGORIES_PIEDRAS_SUCCESS,
    GET_CATEGORY_SUCCESS,
    GET_CATEGORY_FAIL,
} from "../action/types";

const initialState = {
    categories:null,
    categories_piedras:null,
    category:null,
}
export default function Categories(state = initialState, action) {
    const { type, payload } = action;

    switch (type) {
        case GET_CATEGORIES_SUCCESS:
            return{
                ...state,
                categories: payload.categories
            }
        case GET_CATEGORIES_FAIL:
            return{
                ...state,
                categories:null
            }
        case GET_CATEGORIES_PIEDRAS_SUCCESS:
                return{
                    ...state,
                    categories_piedras: payload.categories
                }
        case GET_CATEGORIES_PIEDRAS_FAIL:
                return{
                    ...state,
                    categories_piedras:null
                }
        case GET_CATEGORY_SUCCESS: 
            return{
                ...state,
                category:payload.category
            }
        case GET_CATEGORY_FAIL:
            return{
                ...state,
                category:null
            }
    
        default: return state
    }
}