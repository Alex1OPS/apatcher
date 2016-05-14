/*
  Автор:                Богомолов А.В.
  Дата:                 %date%
  Номер патча:          %ver%
  Номер тикета:         
  Новые объекты:        
  Измененные объекты:   flexy-529004.sql, DIS_MASS_PROCESS.pck
  Удаленные объекты:    
  Комментарий:     	Вот такой комментарий
  
    Создан: %timestamp%
    Список включённых файлов: %changed%


*/


@@ ..\sysobjects\init\flexy\flexy-529004.sql
@@ ..\sysobjects\packages\DIS_MASS_PROCESS.pck
/


-- Откомпилируем все невалидные объекты
begin
  dbms_utility.compile_schema(schema => user, compile_all => false, reuse_settings => true);
end;
/

update FW_VERSION_PROJECT set N_DATABASE_VER = %ver% where V_PROJECT = 'DISC';
commit
/
