try{
    const tryFill=()=>{
        const code=Array.from(document.querySelectorAll('div,span,b,strong')).map(el=>el.innerText.trim()).find(txt=>/^\d{4}$/.test(txt));
        const input=Array.from(document.querySelectorAll('input')).find(i=>i.placeholder.includes("التحقق")||i.placeholder.toLowerCase().includes("captcha"));
        if(code&&input){input.value=code;input.dispatchEvent(new Event('input',{bubbles:true}));}
        else{setTimeout(tryFill,500);}
    };
    tryFill();
}catch(e){console.error('Error:',e);}
