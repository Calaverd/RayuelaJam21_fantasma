
function checkName(var_name, input){
    console.log('Set ',var_name,input);
    setVarValue(var_name,input);
    if(/\d/.test(input)){
        return 0;
    }
    return 1;
};

loadJsonData('./assets/data.dat');