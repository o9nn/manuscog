" Vim syntax file for Limbo programming language
" Language:    Limbo
" Maintainer:  manuscog
" Last Change: 2026

if exists("b:current_syntax")
  finish
endif

" Keywords
syn keyword limboKeyword    implement include import
syn keyword limboKeyword    module adt fn con
syn keyword limboKeyword    self ref chan of
syn keyword limboKeyword    array list to
syn keyword limboKeyword    if else for while do
syn keyword limboKeyword    case alt break continue
syn keyword limboKeyword    return exit spawn
syn keyword limboKeyword    load pick tagof
syn keyword limboKeyword    hd tl len

" Types
syn keyword limboType       int big real byte string
syn keyword limboType       nil

" Constants
syn keyword limboConstant   PATH

" Strings
syn region limboString      start=/"/ skip=/\\"/ end=/"/
syn region limboString      start=/'/ skip=/\\'/ end=/'/

" Comments
syn region limboComment     start=/#/ end=/$/

" Numbers
syn match limboNumber       /\<\d\+\>/
syn match limboNumber       /\<0[xX][0-9a-fA-F]\+\>/
syn match limboNumber       /\<\d\+\.\d*\>/

" Highlighting
hi def link limboKeyword    Keyword
hi def link limboType       Type
hi def link limboConstant   Constant
hi def link limboString     String
hi def link limboComment    Comment
hi def link limboNumber     Number

let b:current_syntax = "limbo"
