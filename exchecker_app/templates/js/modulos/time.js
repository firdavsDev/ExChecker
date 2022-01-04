/*
 * Convert a number of 1 digit in 2 digits
 */
function two_digits(n){
	if (n<10) n='0'+n;
	return n;
}

/*
 * day:month:year h:m:s
 */ 
export function time_to_str(time, utc_format){
	let day;
	let month;
	let year;
	let h;
	let m;
	let s;
	let time_zone;
	if (utc_format) {
		day = time.getUTCDate();
		month = time.getUTCMonth()+1;
		year = time.getUTCFullYear();
		h = time.getUTCHours();
		m = time.getUTCMinutes();
		s = time.getUTCSeconds();
		time_zone = '+00:00'
	}else{
		day = time.getDate();
		month = time.getMonth()+1;
		year = time.getFullYear();
		h = time.getHours();
		m = time.getMinutes();
		s = time.getSeconds();
		time_zone = '+00:01'
	}
    
    day = two_digits(day);
    month = two_digits(month);
    h = two_digits(h);
    m = two_digits(m);
    s = two_digits(s);
    let time_str = day + '-' + month + '-' + year + '        ' +
				 h + ":" + m + ":" + s + ' ' + time_zone;
	return time_str;
}

/*
 * 120 seconds ==> 02:00
 */
export function seconds_to_str(seconds){
	let h_decim = seconds/3600;
	let h = Math.floor(h_decim);
	let m_decim = (h_decim - h)*60;
	let m = Math.floor(m_decim);
	let s_decim = (m_decim - m)*60;
	let s = Math.floor(s_decim);
	h = two_digits(h);
	m = two_digits(m);
	s = two_digits(s);
	return h + ":" + m + ":" + s;
}
