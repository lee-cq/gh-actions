# 此文件将会在Shell创建时被加载
# This File will be load when The shell is created.

function sec2min() {
    tms=$1
    test -n "$tms" || read -r tms
    test -n "$tms" || return 1

    _h=$((tms / 3600))  # 小时数
    _m_s=$((tms - _h * 3600))
    _m=$((_m_s / 60 ))
    _s=$((tms - _m * 60 - _h * 3600 ))

    echo "$_h hour $_m minute $_s sec"
} 

alias ll='ls -Ahl'
alias stopout="sec2min < /tmp/stopout"