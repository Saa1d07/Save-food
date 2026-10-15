const initialMeals = [
 {id:1,name:'وجبات دجاج وأرز',category:'وجبات جاهزة',donor:'مطعم مذاق البيت',quantity:18,expiry:2,location:'حي الروضة',distance:'1.2 كم',emoji:'🍱',kind:'ready'},
 {id:2,name:'مخبوزات طازجة متنوعة',category:'مخبوزات',donor:'مخبز السنابل',quantity:30,expiry:3,location:'حي السلامة',distance:'2.4 كم',emoji:'🥐',kind:'bread'},
 {id:3,name:'سلال خضار وفواكه',category:'خضروات وفواكه',donor:'أسواق الخير',quantity:12,expiry:8,location:'حي الصفا',distance:'3.1 كم',emoji:'🥦',kind:'veg'},
 {id:4,name:'حلويات وتوزيعات',category:'حلويات',donor:'حلويات سُكّر',quantity:15,expiry:5,location:'حي الزهراء',distance:'2.0 كم',emoji:'🧁',kind:'sweet'},
 {id:5,name:'وجبات غداء متكاملة',category:'وجبات جاهزة',donor:'مطعم سفرة',quantity:22,expiry:1,location:'حي الفيصلية',distance:'1.8 كم',emoji:'🍛',kind:'ready'},
 {id:6,name:'خبز ومعجنات',category:'مخبوزات',donor:'فرن الحارة',quantity:25,expiry:4,location:'حي النعيم',distance:'4.2 كم',emoji:'🥖',kind:'bread'}
];
let meals = [...initialMeals];
const reserved = new Set();
const grid = document.getElementById('mealGrid');
const fmtExpiry = h => h <= 1 ? 'ينتهي خلال ساعة' : `ينتهي خلال ${h} ساعات`;
function renderMeals(){
 const q=document.getElementById('searchInput').value.trim().toLowerCase();
 const cat=document.getElementById('categoryFilter').value;
 const sort=document.getElementById('sortFilter').value;
 let shown=meals.filter(m=>(cat==='all'||m.category===cat)&&(`${m.name} ${m.donor} ${m.location}`).toLowerCase().includes(q));
 shown.sort((a,b)=>sort==='quantity'?b.quantity-a.quantity:a.expiry-b.expiry);
 document.getElementById('availableCount').textContent=24+meals.length-initialMeals.length-reserved.size;
 if(!shown.length){grid.innerHTML='<div class="empty">لا توجد وجبات مطابقة لبحثك. جرّب تغيير التصنيف أو كلمة البحث.</div>';return;}
 grid.innerHTML=shown.map(m=>`<article class="meal-card"><div class="meal-cover ${m.kind}"><span class="badge">${m.category}</span><span>${m.emoji}</span><span class="qty">${m.quantity} وجبة</span></div><div class="meal-body"><h3>${escapeHtml(m.name)}</h3><p class="donor">${escapeHtml(m.donor)}</p><div class="meal-meta"><span>◷ ${fmtExpiry(m.expiry)}</span><span>⌖ ${escapeHtml(m.location)}</span></div><div class="meal-footer"><span class="distance">↗ ${m.distance||'موقع مضاف'}</span><button class="reserve" data-id="${m.id}" ${reserved.has(m.id)?'disabled':''}>${reserved.has(m.id)?'تم الحجز ✓':'احجز الوجبات'}</button></div></div></article>`).join('');
}
function escapeHtml(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function toast(msg){const t=document.getElementById('toast');t.textContent=msg;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),2800)}
grid.addEventListener('click',e=>{const b=e.target.closest('button[data-id]');if(!b)return;const id=Number(b.dataset.id);if(reserved.has(id))return;reserved.add(id);renderMeals();toast('تم تسجيل طلب الحجز في النموذج التجريبي بنجاح.');});
['searchInput','categoryFilter','sortFilter'].forEach(id=>document.getElementById(id).addEventListener('input',renderMeals));
document.getElementById('showAll').addEventListener('click',()=>{document.getElementById('searchInput').value='';document.getElementById('categoryFilter').value='all';renderMeals();});
document.getElementById('donateForm').addEventListener('submit',e=>{e.preventDefault();const f=new FormData(e.target);const expiryDate=new Date(f.get('expiry'));const hours=Math.max(1,Math.round((expiryDate-Date.now())/3600000));if(expiryDate<=new Date()){document.getElementById('formMessage').textContent='يرجى اختيار وقت انتهاء في المستقبل.';return;}const kindMap={'وجبات جاهزة':'ready','مخبوزات':'bread','خضروات وفواكه':'veg','حلويات':'sweet'};const emojiMap={'وجبات جاهزة':'🍱','مخبوزات':'🥐','خضروات وفواكه':'🥦','حلويات':'🧁'};meals.unshift({id:Date.now(),name:f.get('name'),category:f.get('category'),donor:f.get('donor'),quantity:Number(f.get('quantity')),expiry:hours,location:f.get('location'),distance:'مضاف حديثًا',emoji:emojiMap[f.get('category')],kind:kindMap[f.get('category')]});e.target.reset();document.getElementById('formMessage').textContent='';renderMeals();toast('تمت إضافة الفائض إلى القائمة التجريبية.');document.getElementById('meals').scrollIntoView({behavior:'smooth'});});
renderMeals();
