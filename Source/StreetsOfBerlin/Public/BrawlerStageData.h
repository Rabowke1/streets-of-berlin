#pragma once

#include "CoreMinimal.h"
#include "BrawlerTypes.h"

/** Eine Gegnergruppe innerhalb eines Kampfes */
struct FSpawnGroup
{
	TArray<FName> Enemies;
	/** Gruppe erscheint, sobald hoechstens so viele Gegner leben ... */
	int32 WhenAliveAtMost = 0;
	/** ... oder spaetestens nach dieser Zeit seit dem letzten Spawn */
	float MaxDelay = 12.f;
};

/** Ein Kampf-Abschnitt: Kamera wird gesperrt, bis alle Gruppen besiegt sind */
struct FEncounter
{
	float TriggerX = 0.f;
	float LockCenterX = 0.f;
	TArray<FSpawnGroup> Groups;
	bool bBoss = false;
};

struct FPropSpawn
{
	FName Type;
	float X = 0.f;
	float Depth = 0.f;
	/** Doener, Currywurst, Money oder ein Waffenname */
	FName Drop;
};

struct FWeaponSpawn
{
	FName Type;
	float X = 0.f;
	float Depth = 0.f;
};

/** Kulissen-Abschnitt einer Stage (Himmel, Fassaden-Kacheln, Boden, Vordergrund) */
struct FStageArea
{
	float StartX = 0.f;
	float EndX = 0.f;
	TArray<FString> Walls;
	FString Floor;
	FString Sky;
	FString Foreground;
	TArray<float> ForegroundX;
};

struct FStageDef
{
	FString Name;
	FString Title;
	TArray<FStageArea> Areas;
	TArray<FEncounter> Encounters;
	TArray<FPropSpawn> Props;
	TArray<FWeaponSpawn> Weapons;
};

/** Werte einer Waffe (entspricht web/js/data.js WEAPONS) */
struct FWeaponDef
{
	FName Type;
	FString DisplayName;
	float Damage = 10.f;
	float Reach = 130.f;
	int32 Durability = 8;
	EHitType HitType = EHitType::Heavy;
	float ThrowDamage = 14.f;
	/** Haltewinkel relativ zum Unterarm (Grad) */
	float HoldAngle = 80.f;
	float FPS = 13.f;
};

namespace BrawlerData
{
	/** Alle Stages in Spielreihenfolge */
	const TArray<FStageDef>& GetStages();

	/** Waffendaten; liefert nullptr fuer unbekannte Namen */
	const FWeaponDef* GetWeapon(FName Type);
	bool IsWeapon(FName Type);

	/** Angriff fuer einen Schwung mit der Waffe */
	FBrawlerAttack MakeWeaponAttack(FName Type);
}
