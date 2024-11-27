import axios from "axios";
import {
    GET_CATEGORIES_FAIL,
    GET_CATEGORIES_SUCCESS,
    GET_CATEGORIES_PIEDRAS_FAIL,
    GET_CATEGORIES_PIEDRAS_SUCCESS,
    GET_CATEGORY_SUCCESS,
    GET_CATEGORY_FAIL,
   
 } from "./types";
const prod=""

export const get_categories = () => async dispatch =>{
    const config = {
        headers: {
            'accept': 'application/json'
        }
    };
    try{
        const res = await axios.get(`${import.meta.env.VITE_API_URL}/api/category/categories`, config)
        if(res.status===200) {
            dispatch({
                type: GET_CATEGORIES_SUCCESS,
                payload: res.data
            })
        }else{
            dispatch({
                type:GET_CATEGORIES_FAIL
            });
        }
    }catch(err) {
        dispatch({
            type:GET_CATEGORIES_FAIL
        });
    }
}

export const get_categories_piedras = () => async dispatch =>{
    const config = {
        headers: {
            'accept': 'application/json'
        }
    };
    try{
        const res = await axios.get(`${import.meta.env.VITE_API_URL}/api/category/piedrascategory`, config)
        if(res.status===200) {
            dispatch({
                type: GET_CATEGORIES_PIEDRAS_SUCCESS,
                payload: res.data
            })
        }else{
            dispatch({
                type:GET_CATEGORIES_PIEDRAS_FAIL
            });
        }
    }catch(err) {
        dispatch({
            type:GET_CATEGORIES_PIEDRAS_FAIL
        });
    }
}
export const get_category = (categoryId) => async dispatch => {
    const config = {
        headers: {
            'accept': 'application/json'
        }
    };
    try{
        const res = await axios.get(`${import.meta.env.VITE_API_URL}/api/category/get-category/${categoryId}`, config)
        if(res.status===200) {
            dispatch({
                type: GET_CATEGORY_SUCCESS,
                payload: res.data
            })
        }else{
            dispatch({
                type:GET_CATEGORY_FAIL
            });
        }
    }catch(err) {
        dispatch({
            type:GET_CATEGORY_FAIL
        });
    }
}


