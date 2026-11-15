export const clamp=(x,a=0,b=1)=>Math.min(b,Math.max(a,x));
export const easeOut=x=>1-Math.pow(1-x,3);
export const easeInOut=x=>x<.5?4*x*x*x:1-Math.pow(-2*x+2,3)/2;
export const back=x=>{const c=1.6;return 1+(c+1)*Math.pow(x-1,3)+c*Math.pow(x-1,2)};
/** 0..1 progress of t through [a, a+d], eased */
export const P=(t,a,d,e=easeOut)=>e(clamp((t-a)/d));
/** fade + rise an element in at `a` over `d`, and optionally out at `o` */
export function show(el,t,a,d=.5,{y=30,x=0,s=1,o=null,od=.35,ease=easeOut}={}){
  let p=P(t,a,d,ease);
  if(o!=null) p*=1-P(t,o,od,x=>x);
  el.style.opacity=p;
  const q=P(t,a,d,ease);
  el.style.translate=`${x*(1-q)}px ${y*(1-q)}px`;
  if(s!==1) el.style.scale=String(s+(1-s)*q);
}
/** type text in from `a` at `cps` chars per second */
export function type(el,text,t,a,cps=40,caret=true){
  const n=Math.floor(clamp((t-a)*cps,0,text.length));
  el.textContent=text.slice(0,n);
  if(caret&&t>=a&&(n<text.length||Math.floor(t*2)%2===0)){const c=document.createElement('span');c.className='caret';el.appendChild(c)}
  return n>=text.length;
}
/** a whole-shot fade at its edges */
export function edges(root,t,dur,i=.35,o=.4){root.style.opacity=Math.min(P(t,0,i,x=>x),1-P(t,dur-o,o,x=>x))}
export const fontsReady=()=>document.fonts.ready;
