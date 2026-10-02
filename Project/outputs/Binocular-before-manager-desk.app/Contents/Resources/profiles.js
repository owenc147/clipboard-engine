// Public Sleeper lookup profiles on this Mac, not authenticated app accounts.
function storedProfiles(){try{return JSON.parse(localStorage.getItem('binocularProfiles')||'[]').filter(x=>typeof x==='string'&&/^[A-Za-z0-9_-]+$/.test(x))}catch{return []}}
function updateProfilePicker(){
 const current=(context.user||'').toLowerCase(),profiles=storedProfiles();
 if(current&&!profiles.includes(current)){profiles.push(current);localStorage.setItem('binocularProfiles',JSON.stringify(profiles))}
 const picker=$('saved-profiles');picker.replaceChildren();
 for(const user of profiles){const option=document.createElement('option');option.value=user;option.textContent='@'+user;option.selected=user===current;picker.append(option)}
 picker.disabled=profiles.length<2;
 if(current)$('user').value=current;
}
const receiveBeforeProfiles=window.receive;
window.receive=data=>{const previous=context.user;receiveBeforeProfiles(data);if(previous&&previous!==context.user){suggestionDraft='';suggestionCategory='Idea'}updateProfilePicker()};
$('saved-profiles').addEventListener('change',event=>{$('user').value=event.target.value;send('refresh')});
