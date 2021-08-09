import{ADD_PERSON} from '../constant'
const initState = [{id:'001',name:'tom', age:19}]
export default function personReducer(prevState=initState, action){
    const {type, data} = action
    switch (type) {
        case ADD_PERSON:
            return [data, ...prevState]
        default:
            return prevState
    }
}