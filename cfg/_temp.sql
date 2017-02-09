/*
  Автор:                __author__
  Дата:                 %date%
  Номер патча:          %ver%
  Номер тикета:         __ticket_num__
  Новые объекты:        __new_objs__
  Измененные объекты:   __modify_objs__
  Удаленные объекты:    __del_objs__
  Комментарий:     	__comment_body__
  
    Создан: %timestamp%
    Список включённых файлов: %changed%


*/

__before_script__

__list_objs__
/


-- Откомпилируем все невалидные объекты
begin
  dbms_utility.compile_schema(schema => user, compile_all => false, reuse_settings => true);
end;
/

update FW_VERSION_PROJECT set N_DATABASE_VER = %ver% where V_PROJECT = '__project__';
commit
/
